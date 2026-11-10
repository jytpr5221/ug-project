"""Loading + sampling of the finfact training schema for the POC evaluation.

Ground truth used here
----------------------
* actual_misinfo_label : from the record's ``label`` field (true -> TRUE,
  false -> FALSE). NEI records have no clear binary ground truth, so they are
  skipped by default (set include_nei=True to keep them).
* actual_severity_label: from the record's ``severity`` field (low/medium/high),
  uppercased for consistency with model output.

Only the ``claim`` text is ever exposed to the model (see prompts.build_prompt).
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ACTUAL_LABEL_MAP = {"true": "TRUE", "false": "FALSE"}
SEVERITY_VALUES = {"low", "medium", "high"}


def load_records(path: str | Path, include_nei: bool = False) -> tuple[list[dict], dict]:
    """Return (records, stats).

    Each record: {claim, actual_misinfo_label, actual_severity_label}
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    records: list[dict] = []
    skipped_nei = skipped_bad = 0
    for row in data:
        claim = (row.get("claim") or "").strip()
        raw_label = (row.get("label") or "").strip().lower()
        raw_sev = (row.get("severity") or "").strip().lower()

        if not claim or raw_sev not in SEVERITY_VALUES:
            skipped_bad += 1
            continue
        if raw_label == "nei" and not include_nei:
            skipped_nei += 1
            continue
        actual = ACTUAL_LABEL_MAP.get(raw_label)
        if actual is None and not include_nei:
            skipped_bad += 1
            continue
        records.append(
            {
                "claim": claim,
                "actual_misinfo_label": actual if actual else "NEI",
                "actual_severity_label": raw_sev.upper(),
            }
        )

    stats = {
        "loaded": len(records),
        "skipped_nei": skipped_nei,
        "skipped_missing_fields": skipped_bad,
    }
    return records, stats


def stratified_sample(
    records: list[dict],
    n: int,
    seed: int = 42,
    min_per_stratum: int = 3,
) -> list[dict]:
    """Proportional stratified sample over (actual label x severity).

    Deterministic for a given seed, so a re-run reproduces the same selection
    and a crashed batch can resume by row count.
    """
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
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
    alloc = {
        k: min(len(groups[k]), max(min_per_stratum, int(n * len(groups[k]) / total)))
        for k in keys
    }
    # trim down to n
    guard = 0
    while sum(alloc.values()) > n and guard < 10000:
        k = max(keys, key=lambda k: alloc[k])
        alloc[k] -= 1
        guard += 1
    # pad up to n where capacity remains
    guard = 0
    while sum(alloc.values()) < n and guard < 10000:
        k = max(keys, key=lambda k: len(groups[k]) - alloc[k])
        if len(groups[k]) - alloc[k] <= 0:
            break
        alloc[k] += 1
        guard += 1

    out = []
    for k in keys:
        out.extend(groups[k][: alloc[k]])
    # top-up if any stratum was too small
    if len(out) < n:
        used = {id(rec) for rec in out}
        rest = [rec for bucket in groups.values() for rec in bucket if id(rec) not in used]
        rng.shuffle(rest)
        out.extend(rest[: n - len(out)])
    rng.shuffle(out)
    return out


def summarize(records: list[dict]) -> Counter:
    """Count (actual label, severity) strata - handy for run logs."""
    return Counter(
        (rec["actual_misinfo_label"], rec["actual_severity_label"]) for rec in records
    )
