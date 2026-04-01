from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_JSON_PATH = PROJECT_ROOT / "dataset.json"

PROMPTS_TUNING_DIR = PROJECT_ROOT / "prompts" / "tuning"
PROMPTS_FINAL_DIR = PROJECT_ROOT / "prompts" / "final"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TUNING_OUTPUT_DIR = OUTPUTS_DIR / "tuning"
GENERATION_OUTPUT_DIR = OUTPUTS_DIR / "generation"

TUNING_RAW_DIR = TUNING_OUTPUT_DIR / "raw"
TUNING_PARSED_DIR = TUNING_OUTPUT_DIR / "parsed"
TUNING_FAILED_DIR = TUNING_OUTPUT_DIR / "failed"
TUNING_MANIFEST_DIR = TUNING_OUTPUT_DIR / "manifests"

GENERATION_RAW_DIR = GENERATION_OUTPUT_DIR / "raw"
GENERATION_PARSED_DIR = GENERATION_OUTPUT_DIR / "parsed"
GENERATION_FAILED_DIR = GENERATION_OUTPUT_DIR / "failed"
GENERATION_MANIFEST_DIR = GENERATION_OUTPUT_DIR / "manifests"

for folder in [
    TUNING_RAW_DIR,
    TUNING_PARSED_DIR,
    TUNING_FAILED_DIR,
    TUNING_MANIFEST_DIR,
    GENERATION_RAW_DIR,
    GENERATION_PARSED_DIR,
    GENERATION_FAILED_DIR,
    GENERATION_MANIFEST_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

PROMPT_TUNING_MODEL = "gpt-5.4"
PROMPT_TUNING_REASONING = {"effort": "medium"}

GENERATION_MODELS = {
    "gpt54mini": {
        "provider": "openai",
        "model": "gpt-5.4-mini",
    },
    "claude_sonnet46": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
    },
    "claude_haiku45": {
        "provider": "anthropic",
        "model": "claude-haiku-4-5",
    },
    "gemini_25_pro": {
        "provider": "gemini",
        "model": "gemini-2.5-pro",
    },
    "gemini_25_flash": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
    },
}

DEFAULT_PROMPT_MODE = "zero_shot"
DEFAULT_TRACE_MODE = "trace_only"
DEFAULT_FINAL_PROMPT_NAME = "zero_shot_best"

DEBUG_MAX_CASES = 3
MAX_OUTPUT_TOKENS = 6000
MAX_RETRIES = 3