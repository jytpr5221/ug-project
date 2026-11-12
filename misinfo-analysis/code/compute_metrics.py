"""Builds metrics_v1.md from the prediction files listed in config.MODEL_RUNS.

    python compute_metrics.py
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config

LABEL_CLASSES = ["TRUE", "FALSE", "NEI"]
SEVERITY_CLASSES = ["HIGH", "MEDIUM", "LOW"]


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _evaluate(rows, classes, actual_key, gen_key):
    valid = [r for r in rows if r[actual_key] in classes and r[gen_key] in classes]
    conf = {a: {g: 0 for g in classes} for a in classes}
    for r in valid:
        conf[r[actual_key]][r[gen_key]] += 1
    scores = {}
    for c in classes:
        tp = conf[c][c]
        fp = sum(conf[a][c] for a in classes if a != c)
        fn = sum(conf[c][g] for g in classes if g != c)
        scores[c] = {"support": tp + fn, "prf": _prf(tp, fp, fn)}
    accuracy = sum(conf[c][c] for c in classes) / len(valid) if valid else 0.0
    macro = sum(scores[c]["prf"][2] for c in classes) / len(classes)
    return {"n_valid": len(valid), "n_invalid": len(rows) - len(valid),
            "conf": conf, "scores": scores, "accuracy": accuracy, "macro_f1": macro}


def _fmt(v):
    return f"{v:.3f}"


def _section(title, result, classes):
    md = [f"### {title}", ""]
    md.append(f"- Evaluated rows: **{result['n_valid']}** | Invalid: {result['n_invalid']} "
              f"| Accuracy: **{_fmt(result['accuracy'])}** | Macro-F1: **{_fmt(result['macro_f1'])}**")
    md.append("")
    md.append("| class | support | precision | recall | F1 |")
    md.append("|---|---|---|---|---|")
    for c in classes:
        p, r, f = result["scores"][c]["prf"]
        md.append(f"| **{c}** | {result['scores'][c]['support']} | {_fmt(p)} | {_fmt(r)} | {_fmt(f)} |")
    md.append("")
    md.append("Actual vs generated:")
    md.append("")
    md.append("| actual \\ generated | " + " | ".join(classes) + " |")
    md.append("|---|" + "---|" * len(classes))
    for a in classes:
        md.append(f"| **{a}** | " + " | ".join(str(result["conf"][a][g]) for g in classes) + " |")
    md.append("")
    return md


def main() -> None:
    md = ["# LLM EVALUATION METRICS - V1", "",
          f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
          "- Protocol: batched API calls; only the claim text was sent", ""]

    included = 0
    for label, model in config.MODEL_RUNS:
        path = config.output_for_model(model)
        if not path.exists():
            print(f"skipping {label}: {path} not found")
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        md.append(f"## {label}")
        md.append("")
        md += _section("Claim judgement (TRUE / FALSE / NEI)",
                       _evaluate(rows, LABEL_CLASSES, "actual_misinfo_label", "generated_misinfo_label"),
                       LABEL_CLASSES)
        md += _section("Severity rating (HIGH / MEDIUM / LOW)",
                       _evaluate(rows, SEVERITY_CLASSES, "actual_severity_label", "generated_severity_label"),
                       SEVERITY_CLASSES)
        included += 1
        print(f"included {label}: {len(rows)} rows")

    if not included:
        raise SystemExit("no prediction files found - run run_eval.py first")

    config.METRICS_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {config.METRICS_MD} ({included} models)")


if __name__ == "__main__":
    main()
