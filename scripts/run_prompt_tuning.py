import argparse
import json
from datetime import datetime

from tqdm import tqdm

from config import (
    DEFAULT_PROMPT_MODE,
    DEFAULT_TRACE_MODE,
    DEBUG_MAX_CASES,
    MAX_RETRIES,
    PROMPT_TUNING_MODEL,
    PROMPT_TUNING_REASONING,
    TUNING_FAILED_DIR,
    TUNING_MANIFEST_DIR,
    TUNING_PARSED_DIR,
    TUNING_RAW_DIR,
)
from dataset_loader import iter_bug_cases
from openai_runner import call_openai_with_retry
from prompt_builder import build_tuning_prompt


def parse_csv_arg(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--prompt_mode",
        type=str,
        default=DEFAULT_PROMPT_MODE,
        help='Prompt mode, e.g. "zero_shot"',
    )
    parser.add_argument(
        "--prompt_versions",
        type=str,
        default="v1",
        help='Comma-separated prompt versions, e.g. "v1,v2,v3"',
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
        default=None,
        help="Optional limit on the number of cases after filtering",
    )
    parser.add_argument(
        "--case_ids",
        type=str,
        default="",
        help='Comma-separated case ids, e.g. "DenningSacco_bug_01,NeedhamSchroederPK_bug_01"',
    )

    args = parser.parse_args()

    prompt_versions = parse_csv_arg(args.prompt_versions)
    requested_case_ids = set(parse_csv_arg(args.case_ids))

    all_cases = list(iter_bug_cases())

    if requested_case_ids:
        all_cases = [case for case in all_cases if case["id"] in requested_case_ids]

    if args.max_cases is not None:
        all_cases = all_cases[: args.max_cases]
    elif not requested_case_ids:
        all_cases = all_cases[:DEBUG_MAX_CASES]

    experiment_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    manifest_records = []

    print(f"Prompt tuning model: {PROMPT_TUNING_MODEL}")
    print(f"Prompt mode: {args.prompt_mode}")
    print(f"Prompt versions: {prompt_versions}")
    print(f"Trace mode: {args.trace_mode}")
    print(f"Total cases: {len(all_cases)}")

    if requested_case_ids:
        print("Selected case ids:")
        for case_id in sorted(requested_case_ids):
            print(f"  - {case_id}")

    for prompt_version in prompt_versions:
        run_name = (
            f"{experiment_id}__{PROMPT_TUNING_MODEL}__"
            f"{args.prompt_mode}__{prompt_version}__{args.trace_mode}"
        )

        print(f"\nRunning combo: {run_name}")

        for case in tqdm(all_cases, desc=run_name):
            full_prompt = build_tuning_prompt(
                case=case,
                prompt_mode=args.prompt_mode,
                prompt_version=prompt_version,
                trace_mode=args.trace_mode,
            )

            result = call_openai_with_retry(
                case=case,
                model=PROMPT_TUNING_MODEL,
                full_prompt=full_prompt,
                run_name=run_name,
                raw_dir=TUNING_RAW_DIR,
                parsed_dir=TUNING_PARSED_DIR,
                failed_dir=TUNING_FAILED_DIR,
                max_retries=MAX_RETRIES,
                reasoning=PROMPT_TUNING_REASONING,
            )

            result["prompt_mode"] = args.prompt_mode
            result["prompt_version"] = prompt_version
            result["trace_mode"] = args.trace_mode
            manifest_records.append(result)

    manifest_path = TUNING_MANIFEST_DIR / f"{experiment_id}.json"
    manifest_path.write_text(
        json.dumps(manifest_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nFinished.")
    print(f"Manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()