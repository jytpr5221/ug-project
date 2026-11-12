# LLM EVALUATION METRICS - V1

- Generated: 2026-11-13
- Protocol: batched API calls; only the claim text was sent

## deepseek-ai/DeepSeek-V4.1-Flash (River)

### Claim judgement (TRUE / FALSE / NEI)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.482** | Macro-F1: **0.470**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **TRUE** | 1275 | 0.692 | 0.529 | 0.600 |
| **FALSE** | 1492 | 0.612 | 0.453 | 0.521 |
| **NEI** | 602 | 0.212 | 0.455 | 0.290 |

Actual vs generated:

| actual \ generated | TRUE | FALSE | NEI |
|---|---|---|---|
| **TRUE** | 675 | 216 | 384 |
| **FALSE** | 184 | 676 | 632 |
| **NEI** | 116 | 212 | 274 |

### Severity rating (HIGH / MEDIUM / LOW)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.486** | Macro-F1: **0.457**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **HIGH** | 138 | 0.258 | 0.732 | 0.382 |
| **MEDIUM** | 1788 | 0.564 | 0.451 | 0.501 |
| **LOW** | 1443 | 0.472 | 0.506 | 0.488 |

Actual vs generated:

| actual \ generated | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **HIGH** | 101 | 36 | 1 |
| **MEDIUM** | 166 | 807 | 815 |
| **LOW** | 124 | 589 | 730 |

## gpt-6.1-sol (Merge Gateway)

### Claim judgement (TRUE / FALSE / NEI)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.442** | Macro-F1: **0.436**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **TRUE** | 1275 | 0.624 | 0.547 | 0.583 |
| **FALSE** | 1492 | 0.591 | 0.316 | 0.412 |
| **NEI** | 602 | 0.221 | 0.533 | 0.312 |

Actual vs generated:

| actual \ generated | TRUE | FALSE | NEI |
|---|---|---|---|
| **TRUE** | 698 | 195 | 382 |
| **FALSE** | 270 | 471 | 751 |
| **NEI** | 150 | 131 | 321 |

### Severity rating (HIGH / MEDIUM / LOW)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.511** | Macro-F1: **0.474**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **HIGH** | 138 | 0.241 | 0.826 | 0.373 |
| **MEDIUM** | 1788 | 0.619 | 0.414 | 0.496 |
| **LOW** | 1443 | 0.511 | 0.602 | 0.553 |

Actual vs generated:

| actual \ generated | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **HIGH** | 114 | 18 | 6 |
| **MEDIUM** | 223 | 741 | 824 |
| **LOW** | 136 | 439 | 868 |

## gemini-3.5-flash-lite (Google)

### Claim judgement (TRUE / FALSE / NEI)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.553** | Macro-F1: **0.511**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **TRUE** | 1275 | 0.643 | 0.653 | 0.648 |
| **FALSE** | 1492 | 0.680 | 0.562 | 0.615 |
| **NEI** | 602 | 0.230 | 0.322 | 0.269 |

Actual vs generated:

| actual \ generated | TRUE | FALSE | NEI |
|---|---|---|---|
| **TRUE** | 832 | 185 | 258 |
| **FALSE** | 263 | 838 | 391 |
| **NEI** | 198 | 210 | 194 |

### Severity rating (HIGH / MEDIUM / LOW)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.455** | Macro-F1: **0.412**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **HIGH** | 138 | 0.176 | 0.819 | 0.290 |
| **MEDIUM** | 1788 | 0.583 | 0.332 | 0.423 |
| **LOW** | 1443 | 0.483 | 0.572 | 0.524 |

Actual vs generated:

| actual \ generated | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **HIGH** | 113 | 19 | 6 |
| **MEDIUM** | 316 | 594 | 878 |
| **LOW** | 212 | 405 | 826 |

## gpt-oss-120b (Groq)

### Claim judgement (TRUE / FALSE / NEI)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.309** | Macro-F1: **0.304**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **TRUE** | 1275 | 0.544 | 0.176 | 0.266 |
| **FALSE** | 1492 | 0.377 | 0.284 | 0.324 |
| **NEI** | 602 | 0.215 | 0.654 | 0.324 |

Actual vs generated:

| actual \ generated | TRUE | FALSE | NEI |
|---|---|---|---|
| **TRUE** | 224 | 543 | 508 |
| **FALSE** | 139 | 424 | 929 |
| **NEI** | 49 | 159 | 394 |

### Severity rating (HIGH / MEDIUM / LOW)

- Evaluated rows: **3369** | Invalid: 0 | Accuracy: **0.470** | Macro-F1: **0.410**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **HIGH** | 138 | 0.219 | 0.507 | 0.306 |
| **MEDIUM** | 1788 | 0.578 | 0.257 | 0.356 |
| **LOW** | 1443 | 0.467 | 0.729 | 0.569 |

Actual vs generated:

| actual \ generated | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **HIGH** | 70 | 32 | 36 |
| **MEDIUM** | 163 | 460 | 1165 |
| **LOW** | 87 | 304 | 1052 |
