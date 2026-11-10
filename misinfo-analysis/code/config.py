"""Central configuration for the LLM evaluation (POC v1).

Everything you normally want to change lives here (model, paths, run size).
API keys are NEVER hard-coded: they are read from the environment by
llm_client.LLMClient (see PROVIDERS there for provider -> env var mapping).
"""

from pathlib import Path

# --- paths -----------------------------------------------------------------
EVAL_DIR = Path(__file__).resolve().parent            # .../misinfo-analysis/code
PROJECT_ROOT = EVAL_DIR.parent                        # .../misinfo-analysis
INPUT_SCHEMA = PROJECT_ROOT / "datasets" / "finfact_training_schema.json"
RESULTS_DIR = EVAL_DIR / "results"
PREDICTIONS_CSV = RESULTS_DIR / "llm_predictions_v1.csv"
SELECTION_JSON = RESULTS_DIR / "selected_records_v1.json"
METRICS_MD = EVAL_DIR / "metrics_v1.md"

# --- model -----------------------------------------------------------------
# Unified interface: to switch models later, change only PROVIDER and MODEL
# (plus the matching API key env var). See llm_client.PROVIDERS.
PROVIDER = "river"                                # river | deepseek | openai | openrouter
MODEL = "deepseek-ai/DeepSeek-V4.1-Flash"         # River-served DeepSeek (see docs)

# --- run settings ----------------------------------------------------------
N_CALLS = None                  # None = label ALL records; set an int to cap
BATCH_SIZE = 300                # claims per API call (one call per batch)
BATCH_PAUSE = 3.0               # seconds of pause between batches
SEED = 42                       # shuffles records deterministically (resume-safe)
INCLUDE_NEI = True              # all records are in scope; NEI is a label
TEMPERATURE = 0.0
MAX_TOKENS = 16384              # one output line per claim (up to 300 lines)
CLIENT_TIMEOUT = 300            # seconds per HTTP call (batch answers take longer)
