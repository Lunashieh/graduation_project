from pathlib import Path

# Project root = the parent of the scripts/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset file
DATASET_JSON_PATH = PROJECT_ROOT / "dataset.json"

# Prompt folder
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Output folders
OUTPUT_DIR = PROJECT_ROOT / "outputs"
RAW_DIR = OUTPUT_DIR / "raw"
PARSED_DIR = OUTPUT_DIR / "parsed"
FAILED_DIR = OUTPUT_DIR / "failed"
MANIFEST_DIR = OUTPUT_DIR / "manifests"

# Make sure output folders exist
for folder in [RAW_DIR, PARSED_DIR, FAILED_DIR, MANIFEST_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Models plan to use
GENERATOR_MODELS = [
    "gpt-4o-mini",
    "gpt-5-mini",
    "o3-mini",
    "gpt-4o",
]

# Prompt modes
PROMPT_MODES = [
    "zero_shot",
    "few_shot",
    "cot",
]

# Your current dataset only clearly supports log-based evidence.
# Keep these modes for future extension, but start with trace_only.
TRACE_MODES = [
    "trace_only",
    "dot_only",
    "trace_and_dot",
]

# Recommended debug defaults
DEFAULT_DEBUG_MODEL = "gpt-4o-mini"
DEFAULT_DEBUG_PROMPT_MODE = "zero_shot"
DEFAULT_DEBUG_TRACE_MODE = "trace_only"

# Small first test
DEBUG_MAX_CASES = 3

# Output control
MAX_OUTPUT_TOKENS = 2000

# Retry setting
MAX_RETRIES = 3