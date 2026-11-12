"""Parses <id>: <label>, <severity> lines from a batch answer."""

import re

_FULL = re.compile(r"(\d{1,4})\s*[:.\)\-]\s*(TRUE|FALSE|NEI)\s*[,;/|\-]?\s*(HIGH|MEDIUM|LOW)", re.I)
_LABEL_ONLY = re.compile(r"(\d{1,4})\s*:\s*(TRUE|FALSE|NEI)\b", re.I)


def parse_batch_response(text, n_claims):
    """Return {0-based claim index: (LABEL, SEVERITY)}; missing ids are absent."""
    out = {}
    for m in _FULL.finditer(text or ""):
        idx = int(m.group(1)) - 1
        if 0 <= idx < n_claims and idx not in out:
            out[idx] = (m.group(2).upper(), m.group(3).upper())
    for m in _LABEL_ONLY.finditer(text or ""):
        idx = int(m.group(1)) - 1
        if 0 <= idx < n_claims and idx not in out:
            out[idx] = (m.group(2).upper(), "INVALID")
    return out
