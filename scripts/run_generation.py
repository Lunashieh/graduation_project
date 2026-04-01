import argparse
import json
from datetime import datetime

from tqdm import tqdm

from anthropic_runner import call_anthropic_with_retry
from config import (
    DEFAULT_FINAL_PROMPT_NAME,
    DEFAULT_TRACE_MODE,
    DEBUG_MAX_CASES,
    GENERATION_FAILED_DIR,
    GENERATION_MANIFEST_DIR,
    GENERATION_MODELS,
    GENERATION_PARSED_DIR,
    GENERATION_RAW_DIR,
    MAX_RETRIES,
)
from dataset_loader import iter_bug_cases
from gemini_runner import call_gemini_with_retry
from openai_runner import call_openai_with_retry
from prompt_builder import build_final_prompt


def parse_csv_arg(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--final_prompt_name",
        type=str,
        default=DEFAULT_FINAL_PROMPT_NAME,
        help='Final prompt file name without .txt, e.g. "zero_shot_best"',
    )
    parser.add_argument(
        "--models",
        type=str,
        default="",
        help='Comma-separated model aliases, e.g. "gpt54mini,claude_sonnet46"',
    )
    parser.add_argument(
        "--trace_mode",
        type=str,
        default=DEFAULT_TRACE_MODE,
        help='Trace mode, e.g. "trace_only"',
    )
    parser.add_argument(
        "--max_cases",
        type=int,
        default=DEBUG_MAX_CASES,
        help="Number of cases to run",
    )

    args = parser.parse_args()

    requested_aliases = parse_csv_arg(args.models)
    model_aliases = requested_aliases if requested_aliases else list(GENERATION_MODELS.keys())

    all_cases = list(iter_bug_cases())[: args.max_cases]
    experiment_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    manifest_records = []

    print(f"Final prompt: {args.final_prompt_name}")
    print(f"Models: {model_aliases}")
    print(f"Trace mode: {args.trace_mode}")
    print(f"Total cases: {len(all_cases)}")

    for alias in model_aliases:
        if alias not in GENERATION_MODELS:
            raise ValueError(f"Unknown model alias: {alias}")

        spec = GENERATION_MODELS[alias]
        provider = spec["provider"]
        model = spec["model"]

        run_name = f"{experiment_id}__{alias}__{args.final_prompt_name}__{args.trace_mode}"

        print(f"\nRunning combo: {run_name}")

        for case in tqdm(all_cases, desc=run_name):
            full_prompt = build_final_prompt(
                case=case,
                prompt_name=args.final_prompt_name,
                trace_mode=args.trace_mode,
            )

            if provider == "openai":
                result = call_openai_with_retry(
                    case=case,
                    model=model,
                    full_prompt=full_prompt,
                    run_name=run_name,
                    raw_dir=GENERATION_RAW_DIR,
                    parsed_dir=GENERATION_PARSED_DIR,
                    failed_dir=GENERATION_FAILED_DIR,
                    max_retries=MAX_RETRIES,
                    reasoning=None,
                )
            elif provider == "anthropic":
                result = call_anthropic_with_retry(
                    case=case,
                    model=model,
                    full_prompt=full_prompt,
                    run_name=run_name,
                    raw_dir=GENERATION_RAW_DIR,
                    parsed_dir=GENERATION_PARSED_DIR,
                    failed_dir=GENERATION_FAILED_DIR,
                    max_retries=MAX_RETRIES,
                )
            elif provider == "gemini":
                result = call_gemini_with_retry(
                    case=case,
                    model=model,
                    full_prompt=full_prompt,
                    run_name=run_name,
                    raw_dir=GENERATION_RAW_DIR,
                    parsed_dir=GENERATION_PARSED_DIR,
                    failed_dir=GENERATION_FAILED_DIR,
                    max_retries=MAX_RETRIES,
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            result["model_alias"] = alias
            result["provider"] = provider
            result["prompt_name"] = args.final_prompt_name
            result["trace_mode"] = args.trace_mode
            manifest_records.append(result)

    manifest_path = GENERATION_MANIFEST_DIR / f"{experiment_id}.json"
    manifest_path.write_text(
        json.dumps(manifest_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nFinished.")
    print(f"Manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()