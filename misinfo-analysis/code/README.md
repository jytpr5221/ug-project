# LLM batch evaluation (POC v1)

Label **every claim** with an LLM and compute precision/recall/F1 into
`metrics_v1.md`.

**Protocol:** one API call receives a numbered list of up to **300 claims**
and must return one line per claim — `<number>: <LABEL>, <SEVERITY>`.
The runner parses the ids back onto the claims, writes the rows to the CSV,
and proceeds to the next batch of 300. The model outputs a 3-class claim
judgement **TRUE / FALSE / NEI** plus a **HIGH/MEDIUM/LOW** severity rating.

- **FALSE** = misinformation (false/misleading about money, markets, companies,
  government finances, personal finance)
- **TRUE** = factually accurate / defensible financial statement
- **NEI** = claim **not related to financial matters** (project definition)
- **Severity** = how serious the topic is if believed (HIGH = loss/fraud/
  insolvency; MEDIUM = decision/market/public-finance stakes with bounded loss;
  LOW = general topic, no direct substantial loss)

## Layout

| File | Purpose |
|---|---|
| `config.py` | All settings: model, provider, paths, batch size, seed |
| `prompts.py` | `BATCH_PROMPT_TEMPLATE` + `SYSTEM_PROMPT` (definitions live here) |
| `llm_client.py` | Unified model-call interface (provider-agnostic, stdlib only, retries) |
| `data_loader.py` | Loads claims + ground truth; deterministic order (resume-safe) |
| `parsing.py` | Parses `<id>: <label>, <severity>` lines back onto claims |
| `run_eval.py` | Batch runner → `results/llm_predictions_v1.csv` |
| `compute_metrics.py` | Metrics → `metrics_v1.md` |

## Quick start

```bash
cd misinfo-analysis/code
export RIVER_API_KEY=rv_...

python3 run_eval.py --dry-run --n 12      # preview the batch prompt, no API calls
python3 run_eval.py                       # ALL 3,369 claims = 12 batch calls
python3 compute_metrics.py                # -> metrics_v1.md
```

Interrupted run? `python3 run_eval.py --resume` (the order is seeded, so it
continues exactly where it stopped — whole batches are saved before moving on).
Restart from scratch with `--overwrite`.

## Switching models later

Only two knobs change (plus the matching API key env var):

```bash
python3 run_eval.py --provider openai --model gpt-4o-mini --batch-size 150
```

Providers are defined in `llm_client.PROVIDERS`; add an entry to support a new
OpenAI-compatible endpoint.

## Output CSV columns

`claim, actual_misinfo_label, generated_misinfo_label, actual_severity_label, generated_severity_label`

Ground truth: `label` (true→TRUE, false→FALSE, NEI→NEI) and `severity` from
`misinfo-analysis/datasets/finfact_training_schema.json`. All 3,369 records are
in scope.

## Caveats

- If a batch answer is missing some ids, the runner does one smaller repair
  call for the stragglers; anything still missing is marked INVALID.
- The schema's NEI originally meant "not enough information" (fact-checker
  verdict); the prompt defines NEI as "not financial-related" — the NEI class
  mixes both notions, so read NEI metrics with care.
- Approx. runtime: 12 batch calls ≈ 4–10 min total (≈4 min in our run); each
  finished batch is flushed to disk, so nothing is lost if interrupted.
