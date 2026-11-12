"""Configuration for the claim-labeling pipeline."""

import os
import re
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
INPUT_SCHEMA = EVAL_DIR.parent / "datasets" / "finfact_training_schema.json"
RESULTS_DIR = EVAL_DIR / "results"
METRICS_MD = EVAL_DIR / "metrics_v1.md"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_env_file(EVAL_DIR / ".env")

# Default model for `python run_eval.py`. Providers are defined in
# llm_client.PROVIDERS: deepseek (River), gemini, merge, groq, groq2, openrouter.
PROVIDER = "deepseek"
MODEL = "deepseek-ai/DeepSeek-V4.1-Flash"

N_CALLS = None          # None = label every record
BATCH_SIZE = 300        # claims per API call
BATCH_PAUSE = 3.0       # seconds between calls
SEED = 42
INCLUDE_NEI = True
TEMPERATURE = 0.0
MAX_TOKENS = 16384
CLIENT_TIMEOUT = 300    # seconds per HTTP request

# Runs shown in metrics_v1.md: (report label, model name)
MODEL_RUNS = [
    ("deepseek-ai/DeepSeek-V4.1-Flash (River)", "deepseek-ai/DeepSeek-V4.1-Flash"),
    ("gpt-6.1-sol (Merge Gateway)", "gpt-6.1-sol"),
    ("gemini-3.5-flash-lite (Google)", "gemini-3.5-flash-lite"),
    ("gpt-oss-120b (Groq)", "openai/gpt-oss-120b"),
]

# Fixed predictions filenames so re-runs resume instead of starting over.
_KNOWN_FILES = {
    "deepseek-ai/DeepSeek-V4.1-Flash": "llm_predictions_deepseek.csv",
    "gpt-6.1-sol": "llm_predictions_gpt61sol.csv",
    "gemini-3.5-flash-lite": "llm_predictions_gemini35flashlite.csv",
    "openai/gpt-oss-120b": "llm_predictions_groq_gptoss120b.csv",
}


def output_for_model(model: str) -> Path:
    name = _KNOWN_FILES.get(model) or "llm_predictions_" + re.sub(r"[^A-Za-z0-9._-]+", "_", model) + ".csv"
    return RESULTS_DIR / name
