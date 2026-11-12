"""Labels all claims with an LLM, one API call per batch of claims.

    python run_eval.py

Uses the model from config.py; call run_all(provider=..., model=...) for a
different one. Finished batches are written to the CSV immediately, so
re-running the command resumes automatically.
"""

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from data_loader import load_records, stratified_sample, summarize
from llm_client import LLMClient
from parsing import parse_batch_response
from prompts import SYSTEM_PROMPT, build_batch_prompt

CSV_HEADER = ["claim", "actual_misinfo_label", "generated_misinfo_label",
              "actual_severity_label", "generated_severity_label"]
VALID_LABELS = {"TRUE", "FALSE", "NEI"}
VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}


def _client(provider=None, model=None) -> LLMClient:
    return LLMClient(provider=provider or config.PROVIDER, model=model or config.MODEL,
                     timeout=config.CLIENT_TIMEOUT, temperature=config.TEMPERATURE,
                     max_tokens=config.MAX_TOKENS)


def _clean(claim: str) -> str:
    return claim.replace("\n", " ").strip()


def _existing_rows(path: Path) -> int:
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        return sum(1 for _ in reader)


def process_batch(client: LLMClient, claims: list[str]) -> list[tuple[str, str]]:
    """Label one batch with a single call (+ one repair call for missing ids)."""
    results = {i: ("INVALID", "INVALID") for i in range(len(claims))}

    reply = None
    error = None
    for _ in (1, 2):
        try:
            reply = client.complete(build_batch_prompt(claims), system=SYSTEM_PROMPT)
            break
        except Exception as exc:
            error = exc
    if reply is None:
        raise error or RuntimeError("batch call failed")

    results.update(parse_batch_response(reply, len(claims)))

    missing = [i for i, (label, _) in results.items() if label == "INVALID"]
    if missing:
        try:
            retry = client.complete(build_batch_prompt([claims[i] for i in missing]), system=SYSTEM_PROMPT)
            for j, idx in enumerate(missing):
                parsed = parse_batch_response(retry, len(missing)).get(j)
                if parsed:
                    results[idx] = parsed
        except Exception:
            pass
    return [results[i] for i in range(len(claims))]


def retry_invalid(provider=None, model=None, output=None) -> int:
    """Re-label the INVALID rows of the predictions file in place."""
    output = Path(output) if output else config.output_for_model(model or config.MODEL)
    if not output.exists():
        return 0
    with open(output, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    bad = [i for i, r in enumerate(rows)
           if r["generated_misinfo_label"] not in VALID_LABELS
           or r["generated_severity_label"] not in VALID_SEVERITIES]
    if not bad:
        return 0

    client = _client(provider, model)
    chunks = [bad[i:i + config.BATCH_SIZE] for i in range(0, len(bad), config.BATCH_SIZE)]
    print(f"repair pass: {len(bad)} INVALID rows in {len(chunks)} calls")
    recovered = 0
    for n, idxs in enumerate(chunks, 1):
        try:
            out = process_batch(client, [_clean(rows[i]["claim"]) for i in idxs])
        except Exception as exc:
            out = [("INVALID", "INVALID")] * len(idxs)
            print(f"  chunk {n}/{len(chunks)} failed: {exc}")
        for i, (label, sev) in zip(idxs, out):
            rows[i]["generated_misinfo_label"] = label
            rows[i]["generated_severity_label"] = sev
            if label in VALID_LABELS:
                recovered += 1
        with open(output, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  chunk {n}/{len(chunks)} done ({recovered}/{len(bad)} recovered)")
        if n < len(chunks):
            time.sleep(config.BATCH_PAUSE)
    return recovered


def run_all(provider=None, model=None, output=None, n=None, fresh=False) -> None:
    """Label all claims with the configured model (see config.py)."""
    model = model or config.MODEL
    output = Path(output) if output else config.output_for_model(model)
    n_select = n if n is not None else config.N_CALLS

    records, stats = load_records(config.INPUT_SCHEMA, include_nei=config.INCLUDE_NEI)
    print(f"loaded {len(records)} records (skipped NEI: {stats['skipped_nei']}, bad: {stats['skipped_bad']})")

    selected = stratified_sample(records, n=n_select if n_select is not None else len(records),
                                 seed=config.SEED)
    print(f"selected {len(selected)} of {len(records)} | {dict(sorted(summarize(selected).items()))}")

    done = _existing_rows(output) if output.exists() and not fresh else 0
    todo = selected[done:]
    if not todo:
        print(f"nothing to do ({done} rows already in {output})")
        print(f"INVALID rows repaired: {retry_invalid(provider, model, output)}")
        return

    client = _client(provider, model)
    batches = [todo[i:i + config.BATCH_SIZE] for i in range(0, len(todo), config.BATCH_SIZE)]
    print(f"{client.provider} / {client.model}: {len(todo)} claims in {len(batches)} calls")

    errors = 0
    with open(output, "a" if done else "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if not done:
            writer.writerow(CSV_HEADER)
        index = done
        for n_batch, chunk in enumerate(batches, 1):
            claims = [_clean(rec["claim"]) for rec in chunk]
            print(f"batch {n_batch}/{len(batches)} (rows {index + 1}-{index + len(chunk)})")
            try:
                results = process_batch(client, claims)
            except Exception as exc:
                results = [("INVALID", "INVALID")] * len(chunk)
                print(f"  failed: {exc}")
            for rec, (label, sev) in zip(chunk, results):
                if label not in VALID_LABELS:
                    errors += 1
                writer.writerow([rec["claim"], rec["actual_misinfo_label"], label,
                                 rec["actual_severity_label"], sev])
            fh.flush()
            ok = sum(1 for label, _ in results if label in VALID_LABELS)
            print(f"  {ok}/{len(chunk)} labelled")
            index += len(chunk)
            if n_batch < len(batches):
                time.sleep(config.BATCH_PAUSE)

    print(f"done -> {output} | INVALID: {errors}")
    if errors:
        print(f"INVALID rows repaired: {retry_invalid(provider, model, output)}")
    print("next: python compute_metrics.py")


if __name__ == "__main__":
    run_all()
