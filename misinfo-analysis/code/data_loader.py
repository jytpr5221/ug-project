"""Loading the dataset and building the processing order."""

import json
import random
from collections import Counter, defaultdict

LABEL_MAP = {"true": "TRUE", "false": "FALSE"}
SEVERITIES = {"low", "medium", "high"}


def load_records(path, include_nei=True):
    """Return (records, stats); record = {claim, actual_misinfo_label, actual_severity_label}."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    records = []
    skipped_nei = skipped_bad = 0
    for row in data:
        claim = (row.get("claim") or "").strip()
        label = (row.get("label") or "").strip().lower()
        severity = (row.get("severity") or "").strip().lower()
        if not claim or severity not in SEVERITIES:
            skipped_bad += 1
            continue
        if label == "nei" and not include_nei:
            skipped_nei += 1
            continue
        records.append({
            "claim": claim,
            "actual_misinfo_label": LABEL_MAP.get(label, "NEI"),
            "actual_severity_label": severity.upper(),
        })
    return records, {"skipped_nei": skipped_nei, "skipped_bad": skipped_bad}


def stratified_sample(records, n, seed=42, min_per_stratum=3):
    """Deterministic proportional sample over (label x severity) strata."""
    groups = defaultdict(list)
    for rec in records:
        groups[(rec["actual_misinfo_label"], rec["actual_severity_label"])].append(rec)

    rng = random.Random(seed)
    for bucket in groups.values():
        rng.shuffle(bucket)

    total = len(records)
    if n >= total:
        out = [rec for bucket in groups.values() for rec in bucket]
        rng.shuffle(out)
        return out

    keys = list(groups)
    alloc = {k: min(len(groups[k]), max(min_per_stratum, int(n * len(groups[k]) / total))) for k in keys}
    while sum(alloc.values()) > n:
        k = max(keys, key=lambda k: alloc[k])
        alloc[k] -= 1
    while sum(alloc.values()) < n:
        k = max(keys, key=lambda k: len(groups[k]) - alloc[k])
        if len(groups[k]) - alloc[k] <= 0:
            break
        alloc[k] += 1

    out = [rec for k in keys for rec in groups[k][:alloc[k]]]
    if len(out) < n:
        used = {id(rec) for rec in out}
        rest = [rec for bucket in groups.values() for rec in bucket if id(rec) not in used]
        rng.shuffle(rest)
        out.extend(rest[: n - len(out)])
    rng.shuffle(out)
    return out


def summarize(records):
    return Counter((rec["actual_misinfo_label"], rec["actual_severity_label"]) for rec in records)
