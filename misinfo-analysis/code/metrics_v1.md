# LLM Evaluation Metrics - POC v1

- Generated: 2026-11-10 14:50
- Predictions file: `/Users/jytpr/dev/ug-project/misinfo-analysis/code/results/llm_predictions_v1.csv`
- Model: `deepseek-ai/DeepSeek-V4.1-Flash`
- Protocol: batch calls of 300 claims; only the claim text was sent
- Rows: 3369 total

## 1. Claim judgement (TRUE / FALSE / NEI)

NEI = claim not related to financial matters (project definition); FALSE = misinformation; TRUE = non-misinformation.

- Evaluated rows: **3369** (out of 3369)
- Invalid outputs: **0** (0.0% of evaluated rows)
- Accuracy: **0.487** | Macro-F1: **0.467**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **TRUE** | 1275 | 0.656 | 0.520 | 0.580 |
| **FALSE** | 1492 | 0.605 | 0.491 | 0.542 |
| **NEI** | 602 | 0.213 | 0.407 | 0.280 |
| **macro avg** | 3369 | | | **0.467** |

| actual \ generated | TRUE | FALSE | NEI |
|---|---|---|---|
| **TRUE** | 663 | 249 | 363 |
| **FALSE** | 220 | 732 | 540 |
| **NEI** | 128 | 229 | 245 |

**Binary view - FALSE (misinformation) vs everything else:**
precision **0.605** | recall **0.491** | F1 **0.542** (TP=732 FP=478 FN=760 TN=1399)

## 2. Severity rating (HIGH / MEDIUM / LOW)

- Evaluated rows: **3369** (out of 3369)
- Invalid outputs: **0** (0.0% of evaluated rows)
- Accuracy: **0.493** | Macro-F1: **0.466**

| class | support | precision | recall | F1 |
|---|---|---|---|---|
| **HIGH** | 138 | 0.275 | 0.725 | 0.398 |
| **MEDIUM** | 1788 | 0.570 | 0.452 | 0.505 |
| **LOW** | 1443 | 0.474 | 0.521 | 0.497 |
| **macro avg** | 3369 | | | **0.466** |

| actual \ generated | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **HIGH** | 100 | 36 | 2 |
| **MEDIUM** | 147 | 809 | 832 |
| **LOW** | 117 | 574 | 752 |

## 3. Sample errors

**Claim judgement mistakes (actual -> predicted):**
- FALSE -> NEI: Is This a Real Image of Tom Cruise's Stunt Doubles?
- FALSE -> NEI: Does Germany Require You To Be Fully Vaccinated Before Receiving Assisted Suicide?
- TRUE -> NEI: Yes, NASA Is Launching 'Armageddon' Mission to Destroy an Asteroid
- NEI -> TRUE: It's clear in our country right now, almost half of American families are a $400 unexpected expense away from complete upheaval.
- TRUE -> NEI: General Motors Sales
- FALSE -> NEI: Is Facebook Deleting an Image of a Cross Carved to Honor Fallen Firefighters?

**Severity mistakes (actual -> predicted):**
- MEDIUM -> LOW: Is This a Real Image of Tom Cruise's Stunt Doubles?
- MEDIUM -> LOW: Does Germany Require You To Be Fully Vaccinated Before Receiving Assisted Suicide?
- LOW -> MEDIUM: It's clear in our country right now, almost half of American families are a $400 unexpected expense away from complete upheaval.
- MEDIUM -> LOW: Is Facebook Deleting an Image of a Cross Carved to Honor Fallen Firefighters?
- MEDIUM -> LOW: Rick Perry Speech
- MEDIUM -> LOW: Did Trump Claim Obama Wrote the Emoluments Clause of U.S. Constitution?

## Notes
- Only the claim text was sent to the model (no justification/evidence).
- Ground truth: `label` and `severity` from `finfact_training_schema.json`.
- Note: the schema's NEI originally came from fact-check verdicts ('not enough information'); the prompt defines NEI as 'not financial-related', so NEI-class metrics mix both notions - read them with care.
- Metrics are computed over valid outputs only; invalid rate reported separately.