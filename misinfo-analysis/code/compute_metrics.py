"""Compute precision / recall / F1 for the POC v1 predictions and write a
markdown report (metrics_v1.md by default).

Tasks
-----
1. Claim judgement (3-class): TRUE / FALSE / NEI
   - FALSE = misinformation, TRUE = non-misinformation,
     NEI     = claim not related to financial matters (project definition).
   - per-class + macro P/R/F1, accuracy, 3x3 confusion matrix, plus a compact
     binary view (FALSE vs everything else) for comparison with the literature.
2. Severity rating (3-class): LOW / MEDIUM / HIGH - per-class and macro P/R/F1.

Invalid model outputs ("INVALID") are excluded from the scores and reported
as an invalid rate (mirrors the Invalid Rate convention of RFC-Bench).

Usage
-----
    python3 compute_metrics.py
    python3 compute_metrics.py --input results/llm_predictions_v1.csv \\
                              --output metrics_v1.md --model-label deepseek-ai/DeepSeek-V4.1-Flash
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config

LABEL_CLASSES = ["TRUE", "FALSE", "NEI"]
SEVERITY_CLASSES = ["HIGH", "MEDIUM", "LOW"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="metrics for POC v1 predictions")
    p.add_argument("--input", type=Path, default=config.PREDICTIONS_CSV)
    p.add_argument("--output", type=Path, default=config.METRICS_MD)
    p.add_argument("--model-label", default=config.MODEL,
                   help="model name shown in the report header")
    return p.parse_args()


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def confusion(rows: list[dict], classes: list[str], actual_key: str, gen_key: str) -> dict:
    conf = {a: {g: 0 for g in classes} for a in classes}
    for r in rows:
        conf[r[actual_key]][r[gen_key]] += 1
    return conf


def per_class_scores(conf: dict, classes: list[str]) -> dict:
    scores = {}
    for c in classes:
        tp = conf[c][c]
        fp = sum(conf[a][c] for a in classes if a != c)
        fn = sum(conf[c][g] for g in classes if g != c)
        scores[c] = {"support": tp + fn, "prf": prf(tp, fp, fn)}
    return scores


def macro_f1(scores: dict, classes: list[str]) -> float:
    return sum(scores[c]["prf"][2] for c in classes) / len(classes)


def fmt(value: float) -> str:
    return f"{value:.3f}"


def render_confusion(conf: dict, classes: list[str]) -> str:
    lines = ["| actual \\ generated | " + " | ".join(classes) + " |",
             "|---|" + "---|" * len(classes)]
    for a in classes:
        lines.append(f"| **{a}** | " + " | ".join(str(conf[a][g]) for g in classes) + " |")
    return "\n".join(lines)


def render_scores(scores: dict, classes: list[str]) -> str:
    lines = ["| class | support | precision | recall | F1 |", "|---|---|---|---|---|"]
    for c in classes:
        s = scores[c]
        p, r, f = s["prf"]
        lines.append(f"| **{c}** | {s['support']} | {fmt(p)} | {fmt(r)} | {fmt(f)} |")
    lines.append(f"| **macro avg** | {sum(scores[c]['support'] for c in classes)} | | "
                 f"| **{fmt(macro_f1(scores, classes))}** |")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"predictions file not found: {args.input} (run run_eval.py first)")

    with open(args.input, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    total = len(rows)

    # ---------- claim judgement (TRUE / FALSE / NEI) --------------------
    lab_rows = [r for r in rows if r["actual_misinfo_label"] in LABEL_CLASSES]
    lab_valid = [r for r in lab_rows if r["generated_misinfo_label"] in LABEL_CLASSES]
    lab_invalid = len(lab_rows) - len(lab_valid)

    lab_conf = confusion(
        [{"a": r["actual_misinfo_label"], "g": r["generated_misinfo_label"]} for r in lab_valid],
        LABEL_CLASSES, "a", "g")
    lab_scores = per_class_scores(lab_conf, LABEL_CLASSES)
    lab_acc = sum(lab_conf[c][c] for c in LABEL_CLASSES) / max(1, len(lab_valid))

    # compact binary view: FALSE (misinformation) vs everything else
    tp = sum(1 for r in lab_valid
             if r["actual_misinfo_label"] == "FALSE" and r["generated_misinfo_label"] == "FALSE")
    fp = sum(1 for r in lab_valid
             if r["actual_misinfo_label"] != "FALSE" and r["generated_misinfo_label"] == "FALSE")
    fn = sum(1 for r in lab_valid
             if r["actual_misinfo_label"] == "FALSE" and r["generated_misinfo_label"] != "FALSE")
    tn = len(lab_valid) - tp - fp - fn
    bin_p, bin_r, bin_f1 = prf(tp, fp, fn)

    # ---------- severity (LOW / MEDIUM / HIGH) --------------------------
    sev_rows = [r for r in rows if r["actual_severity_label"] in SEVERITY_CLASSES]
    sev_valid = [r for r in sev_rows if r["generated_severity_label"] in SEVERITY_CLASSES]
    sev_invalid = len(sev_rows) - len(sev_valid)

    sev_conf = confusion(
        [{"a": r["actual_severity_label"], "g": r["generated_severity_label"]} for r in sev_valid],
        SEVERITY_CLASSES, "a", "g")
    sev_scores = per_class_scores(sev_conf, SEVERITY_CLASSES)
    sev_acc = sum(sev_conf[c][c] for c in SEVERITY_CLASSES) / max(1, len(sev_valid))

    # ---------- error samples ----------------------------------------------
    lab_err = [(r["actual_misinfo_label"], r["generated_misinfo_label"], r["claim"])
               for r in lab_valid if r["actual_misinfo_label"] != r["generated_misinfo_label"]][:6]
    sev_err = [(r["actual_severity_label"], r["generated_severity_label"], r["claim"])
               for r in sev_valid if r["actual_severity_label"] != r["generated_severity_label"]][:6]

    # ---------- report -------------------------------------------------------
    md: list[str] = []
    md.append("# LLM Evaluation Metrics - POC v1")
    md.append("")
    md.append(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"- Predictions file: `{args.input}`")
    md.append(f"- Model: `{args.model_label}`")
    md.append(f"- Protocol: batch calls of {config.BATCH_SIZE} claims; only the claim text was sent")
    md.append(f"- Rows: {total} total")
    md.append("")
    md.append("## 1. Claim judgement (TRUE / FALSE / NEI)")
    md.append("")
    md.append("NEI = claim not related to financial matters (project definition);"
              " FALSE = misinformation; TRUE = non-misinformation.")
    md.append("")
    md.append(f"- Evaluated rows: **{len(lab_valid)}** (out of {len(lab_rows)})")
    md.append(f"- Invalid outputs: **{lab_invalid}**"
              f" ({100 * lab_invalid / max(1, len(lab_rows)):.1f}% of evaluated rows)")
    md.append(f"- Accuracy: **{fmt(lab_acc)}** | Macro-F1: **{fmt(macro_f1(lab_scores, LABEL_CLASSES))}**")
    md.append("")
    md.append(render_scores(lab_scores, LABEL_CLASSES))
    md.append("")
    md.append(render_confusion(lab_conf, LABEL_CLASSES))
    md.append("")
    md.append("**Binary view - FALSE (misinformation) vs everything else:**")
    md.append(f"precision **{fmt(bin_p)}** | recall **{fmt(bin_r)}** | F1 **{fmt(bin_f1)}**"
              f" (TP={tp} FP={fp} FN={fn} TN={tn})")
    md.append("")
    md.append("## 2. Severity rating (HIGH / MEDIUM / LOW)")
    md.append("")
    md.append(f"- Evaluated rows: **{len(sev_valid)}** (out of {len(sev_rows)})")
    md.append(f"- Invalid outputs: **{sev_invalid}**"
              f" ({100 * sev_invalid / max(1, len(sev_rows)):.1f}% of evaluated rows)")
    md.append(f"- Accuracy: **{fmt(sev_acc)}** | Macro-F1: **{fmt(macro_f1(sev_scores, SEVERITY_CLASSES))}**")
    md.append("")
    md.append(render_scores(sev_scores, SEVERITY_CLASSES))
    md.append("")
    md.append(render_confusion(sev_conf, SEVERITY_CLASSES))
    md.append("")
    md.append("## 3. Sample errors")
    md.append("")
    md.append("**Claim judgement mistakes (actual -> predicted):**")
    md += [f"- {a} -> {g}: {c[:140]}" for a, g, c in lab_err] or ["- (none)"]
    md.append("")
    md.append("**Severity mistakes (actual -> predicted):**")
    md += [f"- {a} -> {g}: {c[:140]}" for a, g, c in sev_err] or ["- (none)"]
    md.append("")
    md.append("## Notes")
    md.append("- Only the claim text was sent to the model (no justification/evidence).")
    md.append("- Ground truth: `label` and `severity` from `finfact_training_schema.json`.")
    md.append("- Note: the schema's NEI originally came from fact-check verdicts"
              " ('not enough information'); the prompt defines NEI as 'not financial-related',"
              " so NEI-class metrics mix both notions - read them with care.")
    md.append("- Metrics are computed over valid outputs only; invalid rate reported separately.")

    args.output.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"  judgement: acc={fmt(lab_acc)} macro-F1={fmt(macro_f1(lab_scores, LABEL_CLASSES))} "
          f"(n={len(lab_valid)}, invalid={lab_invalid})")
    print(f"  binary   : precision={fmt(bin_p)} recall={fmt(bin_r)} F1={fmt(bin_f1)}")
    print(f"  severity : acc={fmt(sev_acc)} macro-F1={fmt(macro_f1(sev_scores, SEVERITY_CLASSES))} "
          f"(n={len(sev_valid)}, invalid={sev_invalid})")


if __name__ == "__main__":
    main()
