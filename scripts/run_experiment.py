import argparse
import json
from datetime import datetime

from tqdm import tqdm

from config import (
    GENERATOR_MODELS,
    PROMPT_MODES,
    TRACE_MODES,
    DEFAULT_DEBUG_MODEL,
    DEFAULT_DEBUG_PROMPT_MODE,
    DEFAULT_DEBUG_TRACE_MODE,
    DEBUG_MAX_CASES,
    MAX_RETRIES,
    MANIFEST_DIR,
)
from dataset_loader import iter_bug_cases
from openai_runner import call_model_with_retry
from prompt_builder import build_full_prompt


def parse_csv_arg(value: str):
    """
    Parse a comma-separated command-line argument into a list.
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["debug", "full"],
        default="debug",
        help="debug = small first test, full = larger run"
    )

    parser.add_argument(
        "--models",
        type=str,
        default="",
        help='Comma-separated models, e.g. "gpt-4o-mini,gpt-5-mini"'
    )

    parser.add_argument(
        "--prompt_modes",
        type=str,
        default="",
        help='Comma-separated prompt modes, e.g. "zero_shot,few_shot"'
    )

    parser.add_argument(
        "--prompt_versions",
        type=str,
        default="v1",
        help='Comma-separated prompt versions, e.g. "v1,v2,v3"'
    )

    parser.add_argument(
        "--trace_modes",
        type=str,
        default="",
        help='Comma-separated trace modes, e.g. "trace_only"'
    )

    parser.add_argument(
        "--max_cases",
        type=int,
        default=None,
        help="Optional limit on the number of bug cases"
    )

    args = parser.parse_args()

    all_cases = list(iter_bug_cases())

    if args.max_cases is not None:
        all_cases = all_cases[:args.max_cases]
    elif args.mode == "debug":
        all_cases = all_cases[:DEBUG_MAX_CASES]

    user_models = parse_csv_arg(args.models)
    if user_models:
        models = user_models
    elif args.mode == "debug":
        models = [DEFAULT_DEBUG_MODEL]
    else:
        models = GENERATOR_MODELS

    user_prompt_modes = parse_csv_arg(args.prompt_modes)
    if user_prompt_modes:
        prompt_modes = user_prompt_modes
    elif args.mode == "debug":
        prompt_modes = [DEFAULT_DEBUG_PROMPT_MODE]
    else:
        prompt_modes = PROMPT_MODES

    user_prompt_versions = parse_csv_arg(args.prompt_versions)
    if user_prompt_versions:
        prompt_versions = user_prompt_versions
    else:
        prompt_versions = ["v1"]

    user_trace_modes = parse_csv_arg(args.trace_modes)
    if user_trace_modes:
        trace_modes = user_trace_modes
    elif args.mode == "debug":
        trace_modes = [DEFAULT_DEBUG_TRACE_MODE]
    else:
        trace_modes = TRACE_MODES

    experiment_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    manifest_records = []

    print(f"Total cases to run: {len(all_cases)}")
    print(f"Models: {models}")
    print(f"Prompt modes: {prompt_modes}")
    print(f"Prompt versions: {prompt_versions}")
    print(f"Trace modes: {trace_modes}")

    for model in models:
        for prompt_mode in prompt_modes:
            for prompt_version in prompt_versions:
                for trace_mode in trace_modes:
                    run_name = (
                        f"{experiment_id}__{model}__{prompt_mode}__"
                        f"{prompt_version}__{trace_mode}"
                    )

                    print(f"\nRunning combo: {run_name}")

                    for case in tqdm(all_cases, desc=run_name):
                        full_prompt = build_full_prompt(
                            case=case,
                            prompt_mode=prompt_mode,
                            prompt_version=prompt_version,
                            trace_mode=trace_mode
                        )

                        result = call_model_with_retry(
                            case=case,
                            model=model,
                            full_prompt=full_prompt,
                            run_name=run_name,
                            max_retries=MAX_RETRIES
                        )

                        result["prompt_mode"] = prompt_mode
                        result["prompt_version"] = prompt_version
                        result["trace_mode"] = trace_mode
                        manifest_records.append(result)

    manifest_path = MANIFEST_DIR / f"{experiment_id}.json"
    manifest_path.write_text(
        json.dumps(manifest_records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nFinished.")
    print(f"Manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()