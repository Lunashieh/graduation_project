import time
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from common import collect_text_snippets, object_to_dict, save_json
from config import MAX_OUTPUT_TOKENS
from output_parser import parse_generation_output

load_dotenv()
client = Anthropic()


def extract_text_from_anthropic_response(response) -> str:
    texts: list[str] = []

    for block in getattr(response, "content", []) or []:
        block_type = getattr(block, "type", None)
        block_text = getattr(block, "text", None)
        if block_type == "text" and isinstance(block_text, str) and block_text.strip():
            texts.append(block_text.strip())

    if texts:
        return "\n".join(texts).strip()

    snippets = collect_text_snippets(response)
    if snippets:
        return "\n".join(snippets).strip()

    return ""


def call_anthropic_once(
    case: dict,
    model: str,
    full_prompt: str,
    run_name: str,
    raw_dir: Path,
    parsed_dir: Path,
    failed_dir: Path,
) -> dict:
    sample_id = case["id"]
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    raw_path = raw_dir / run_name / f"{sample_id}__{timestamp}.json"
    parsed_path = parsed_dir / run_name / f"{sample_id}__{timestamp}.json"
    failed_path = failed_dir / run_name / f"{sample_id}__{timestamp}.json"

    try:
        response = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[{"role": "user", "content": full_prompt}],
        )

        response_dict = object_to_dict(response)
        raw_text = extract_text_from_anthropic_response(response)
        usage = object_to_dict(getattr(response, "usage", None))

        save_json(
            raw_path,
            {
                "provider": "anthropic",
                "sample_id": sample_id,
                "protocol": case["protocol"],
                "bug_id": case["bug_id"],
                "model": model,
                "timestamp": timestamp,
                "prompt": full_prompt,
                "response": response_dict,
                "response_text": raw_text,
            },
        )

        parsed = parse_generation_output(raw_text)

        save_json(
            parsed_path,
            {
                "provider": "anthropic",
                "sample_id": sample_id,
                "protocol": case["protocol"],
                "bug_id": case["bug_id"],
                "model": model,
                "timestamp": timestamp,
                "usage": usage,
                "result": parsed.model_dump(),
            },
        )

        return {
            "provider": "anthropic",
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "status": "success",
            "raw_path": str(raw_path),
            "parsed_path": str(parsed_path),
        }

    except Exception as e:
        save_json(
            failed_path,
            {
                "provider": "anthropic",
                "sample_id": sample_id,
                "protocol": case["protocol"],
                "bug_id": case["bug_id"],
                "model": model,
                "timestamp": timestamp,
                "prompt": full_prompt,
                "error": str(e),
            },
        )

        return {
            "provider": "anthropic",
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "status": "failed",
            "error": str(e),
            "failed_path": str(failed_path),
        }


def call_anthropic_with_retry(
    case: dict,
    model: str,
    full_prompt: str,
    run_name: str,
    raw_dir: Path,
    parsed_dir: Path,
    failed_dir: Path,
    max_retries: int = 3,
) -> dict:
    last_result = None

    for attempt in range(max_retries):
        result = call_anthropic_once(
            case=case,
            model=model,
            full_prompt=full_prompt,
            run_name=run_name,
            raw_dir=raw_dir,
            parsed_dir=parsed_dir,
            failed_dir=failed_dir,
        )
        last_result = result

        if result["status"] == "success":
            return result

        time.sleep(2 * (attempt + 1))

    return last_result