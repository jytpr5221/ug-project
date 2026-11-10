"""POC v1 batch runner: label ALL claims via batch API calls (300 claims/call).

Design
------
* One API call receives up to ``--batch-size`` (default 300) numbered claims
  and must return one line per claim: ``<number>: <LABEL>, <SEVERITY>``.
* The runner parses the ids back onto the claims, writes every row to the CSV
  immediately after each batch, then moves on to the next batch.
* Missing/partial ids get ONE smaller retry call; still-missing ids become
  "INVALID" rather than aborting the run.

Output CSV columns:
    claim, actual_misinfo_label, generated_misinfo_label,
    actual_severity_label, generated_severity_label

Examples
--------
    python3 run_eval.py --dry-run --n 12       # preview the batch prompt
    python3 run_eval.py                        # ALL records, 300/batch
    python3 run_eval.py --resume               # continue an interrupted run
    python3 run_eval.py --provider openai --model gpt-4o-mini --n 300
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from data_loader import load_records, stratified_sample, summarize
from llm_client import PROVIDERS, LLMClient
from parsing import parse_batch_response
from prompts import SYSTEM_PROMPT, build_batch_prompt

CSV_HEADER = [
    "claim",
    "actual_misinfo_label",
    "generated_misinfo_label",
    "actual_severity_label",
    "generated_severity_label",
]

VALID_LABELS = {"TRUE", "FALSE", "NEI"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM batch evaluation (POC v1)")
    p.add_argument("--input", type=Path, default=config.INPUT_SCHEMA)
    p.add_argument("--output", type=Path, default=config.PREDICTIONS_CSV)
    p.add_argument("--n", type=int, default=config.N_CALLS,
                   help="cap the number of records (default: ALL records)")
    p.add_argument("--batch-size", type=int, default=config.BATCH_SIZE,
                   help="claims per API call (default 300)")
    p.add_argument("--batch-pause", type=float, default=config.BATCH_PAUSE,
                   help="seconds of pause between batch calls")
    p.add_argument("--seed", type=int, default=config.SEED)
    p.add_argument("--provider", default=config.PROVIDER, choices=sorted(PROVIDERS))
    p.add_argument("--model", default=config.MODEL)
    p.add_argument("--base-url", default=None)
    p.add_argument("--api-key", default=None, help="else read from env var")
    p.add_argument("--timeout", type=int, default=config.CLIENT_TIMEOUT)
    p.add_argument("--temperature", type=float, default=config.TEMPERATURE)
    p.add_argument("--max-tokens", type=int, default=config.MAX_TOKENS)
    p.add_argument("--include-nei", action="store_true", default=config.INCLUDE_NEI)
    p.add_argument("--dry-run", action="store_true", help="no API calls; preview")
    p.add_argument("--resume", action="store_true", help="continue existing CSV")
    p.add_argument("--overwrite", action="store_true", help="restart the CSV")
    return p.parse_args()


def _existing_rows(path: Path) -> int:
    # Count logical CSV rows (claims may contain embedded newlines).
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # header
        return sum(1 for _ in reader)


def process_batch(client: LLMClient, chunk: list[dict]) -> list[tuple[str, str]]:
    """Label one chunk of claims with a single API call (+ one repair call).

    Returns a list of (label, severity) in the same order as ``chunk``;
    unparseable entries come back as ("INVALID", "INVALID").
    """
    claims = [rec["claim"].replace("\n", " ").strip() for rec in chunk]
    results: dict[int, tuple[str, str]] = {i: ("INVALID", "INVALID") for i in range(len(claims))}

    reply = None
    last_exc: Exception | None = None
    for _attempt in (1, 2):                      # whole-batch retry on failure
        try:
            reply = client.complete(build_batch_prompt(claims), system=SYSTEM_PROMPT)
            break
        except Exception as exc:                 # network / API problem
            last_exc = exc
    if reply is None:
        raise last_exc if last_exc else RuntimeError("batch call failed")

    for idx, value in parse_batch_response(reply, len(claims)).items():
        results[idx] = value

    missing = [i for i, value in results.items() if value[0] == "INVALID"]
    if missing:                                   # one repair call for stragglers
        sub_claims = [claims[i] for i in missing]
        try:
            reply2 = client.complete(build_batch_prompt(sub_claims), system=SYSTEM_PROMPT)
            for j, idx in enumerate(missing):
                parsed = parse_batch_response(reply2, len(sub_claims)).get(j)
                if parsed:
                    results[idx] = parsed
        except Exception:
            pass                                  # stragglers stay INVALID

    return [results[i] for i in range(len(claims))]


def main() -> None:
    args = parse_args()

    records, stats = load_records(args.input, include_nei=args.include_nei)
    print(
        f"loaded {len(records)} usable records from {args.input} "
        f"(skipped NEI: {stats['skipped_nei']}, bad fields: {stats['skipped_missing_fields']})"
    )

    n_select = args.n if args.n is not None else len(records)
    selected = stratified_sample(records, n=n_select, seed=args.seed)
    scope = "all" if n_select >= len(records) else f"{len(selected)} of {len(records)}"
    print(f"selected {len(selected)} records ({scope}) | strata: "
          f"{dict(sorted(summarize(selected).items()))}")

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SELECTION_JSON, "w", encoding="utf-8") as fh:
        json.dump(
            {"seed": args.seed, "n": n_select, "records": selected},
            fh,
            ensure_ascii=False,
            indent=1,
        )
    print(f"selection saved to {config.SELECTION_JSON}")

    if args.dry_run:
        preview_claims = [r["claim"] for r in selected[: min(args.batch_size, len(selected))]]
        prompt = build_batch_prompt(preview_claims)
        print(f"\n--- dry run: batch prompt for {len(preview_claims)} claims "
              f"(truncated to 1600 chars, no API calls) ---\n")
        print(prompt[:1600] + ("\n...[truncated]" if len(prompt) > 1600 else ""))
        print("\ndry run finished - nothing was sent to the model.")
        return

    # ---- resume / overwrite handling --------------------------------------
    output = args.output
    if output.exists() and args.resume:
        done = _existing_rows(output)
        mode = "a"
        print(f"resuming: {done} rows already in {output}")
    elif output.exists() and args.overwrite:
        done, mode = 0, "w"
    elif output.exists():
        raise SystemExit(
            f"{output} already exists - pass --resume to continue "
            f"or --overwrite to restart"
        )
    else:
        done, mode = 0, "w"

    todo = selected[done:]
    if not todo:
        print("nothing to do: all selected records already have predictions.")
        return

    client = LLMClient(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        timeout=args.timeout,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    n_batches = (len(todo) + args.batch_size - 1) // args.batch_size
    print(
        f"calling provider={client.provider} model={client.model} | "
        f"{len(todo)} claims in {n_batches} batch calls of {args.batch_size} "
        f"(est. {n_batches * 1.5:.0f} min)"
    )

    errors = 0
    with open(output, mode, encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if mode == "w":
            writer.writerow(CSV_HEADER)
        for b in range(n_batches):
            chunk = todo[b * args.batch_size:(b + 1) * args.batch_size]
            first = done + b * args.batch_size + 1
            last = first + len(chunk) - 1
            print(f"--- batch {b + 1}/{n_batches} (rows {first}-{last}, one API call) ---")
            try:
                batch_results = process_batch(client, chunk)
            except Exception as exc:
                batch_results = [("INVALID", "INVALID")] * len(chunk)
                print(f"  BATCH FAILED: {exc}")
            batch_valid = sum(1 for label, _ in batch_results if label in VALID_LABELS)
            for rec, (gen_label, gen_sev) in zip(chunk, batch_results):
                if gen_label not in VALID_LABELS:
                    errors += 1
                writer.writerow(
                    [
                        rec["claim"],
                        rec["actual_misinfo_label"],
                        gen_label,
                        rec["actual_severity_label"],
                        gen_sev,
                    ]
                )
                print(
                    f"    {gen_label:>7}/{gen_sev:<6} "
                    f"(actual {rec['actual_misinfo_label']}/{rec['actual_severity_label']}) | "
                    f"{rec['claim'][:60]}"
                )
            fh.flush()
            print(f"  batch done: {batch_valid}/{len(chunk)} labelled")
            if b + 1 < n_batches and args.batch_pause:
                time.sleep(args.batch_pause)

    print(f"\ndone. predictions -> {output}")
    print(f"INVALID rows: {errors}/{len(todo)}")
    print(f"next: python3 {Path(__file__).name.replace('run_eval', 'compute_metrics')}")


if __name__ == "__main__":
    main()
