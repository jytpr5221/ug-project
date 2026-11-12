# Claim labeling pipeline

Labels every claim in the dataset with an LLM and builds the
`LLM EVALUATION METRICS - V1` report.

## Run

```bash
python run_eval.py          # labels all 3,369 claims (model from config.py)
python compute_metrics.py   # -> metrics_v1.md
```

- Default model: DeepSeek-V4.1-Flash via River. Switch by editing `config.py`
  or by calling `run_all(provider="groq", model="openai/gpt-oss-120b")`.
- API keys are read from `.env` (River, Gemini, Merge, Groq, Groq2, OpenRouter).
- Re-running resumes automatically from the saved CSV; `run_all(fresh=True)`
  restarts from scratch.
- Retries are built in: 4 per HTTP call, plus batch-level retries and one
  final pass over INVALID rows.

## How it works

One API call per batch of claims (300 by default): a numbered claim list goes
in, one `<id>: <LABEL>, <SEVERITY>` line per claim comes out, and the ids are
parsed back onto the claims. Only the claim text is sent.

- Claim judgement: `TRUE` / `FALSE` (misinformation) / `NEI` (not related to
  financial matters)
- Severity: `HIGH` (loss/fraud/insolvency) / `MEDIUM` (decision- or
  market-affecting stakes with bounded loss) / `LOW` (general topic)

## Files

| file | purpose |
|---|---|
| `config.py` | default model, paths, batch settings, report registry |
| `prompts.py` | prompt template + label definitions |
| `llm_client.py` | provider registry + HTTP client |
| `data_loader.py` | dataset loading + deterministic processing order |
| `parsing.py` | parses batch answers back onto claims |
| `run_eval.py` | batch runner -> `results/llm_predictions_*.csv` |
| `compute_metrics.py` | builds `metrics_v1.md` |

## Adding a model

1. Run it, e.g. `run_all(provider="openrouter", model="qwen/qwen3.8-flash")`.
2. Add `(label, model)` to `config.MODEL_RUNS`; add the model to
   `config._KNOWN_FILES` if you want a specific filename.
3. `python compute_metrics.py`.

## Caveats

- The dataset's `NEI` originally meant "not enough information"; the prompt
  defines NEI as "not financial-related", so NEI metrics mix both notions.
- Free API tiers have tight per-model quotas (Gemini, Groq). The retry logic
  and the repair pass keep runs recoverable; re-running continues where it
  stopped. Groq needs `BATCH_SIZE = 40` and `MAX_TOKENS = 4096` to fit its
  8k-tokens-per-minute request cap.
