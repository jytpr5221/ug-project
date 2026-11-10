"""Parsing of batch model answers.

One API call per 300 claims; the model returns one line per claim:
    <number>: <TRUE|FALSE|NEI>, <HIGH|MEDIUM|LOW>
``parse_batch_response`` maps those ids back onto claim indices. Anything that
cannot be parsed unambiguously is left out of the result and marked "INVALID"
by the caller.
"""

from __future__ import annotations

import re

# "12: FALSE, HIGH" (also tolerate 12) / 12. / 12 -) -------------------------
_BATCH_FULL = re.compile(
    r"(\d{1,4})\s*[:.\)\-]\s*(TRUE|FALSE|NEI)\s*[,;/|\-]?\s*(HIGH|MEDIUM|LOW)",
    re.IGNORECASE,
)
# label-only fallback (severity missing) - restricted to ":" so that echoed
# numbered claims ("12. Some claim text ...") cannot be mistaken for answers.
_BATCH_LABEL_ONLY = re.compile(r"(\d{1,4})\s*:\s*(TRUE|FALSE|NEI)\b", re.IGNORECASE)


def parse_batch_response(text: str, n_claims: int) -> dict[int, tuple[str, str]]:
    """Map ``<id>: <label>, <severity>`` lines to claim indices.

    Returns {0-based claim index: (LABEL, SEVERITY)}; missing claims are simply
    absent from the dict (the caller marks them INVALID / retries them).
    """
    text = text or ""
    out: dict[int, tuple[str, str]] = {}
    for m in _BATCH_FULL.finditer(text):
        idx = int(m.group(1)) - 1
        if 0 <= idx < n_claims and idx not in out:
            out[idx] = (m.group(2).upper(), m.group(3).upper())
    for m in _BATCH_LABEL_ONLY.finditer(text):
        idx = int(m.group(1)) - 1
        if 0 <= idx < n_claims and idx not in out:
            out[idx] = (m.group(2).upper(), "INVALID")
    return out
