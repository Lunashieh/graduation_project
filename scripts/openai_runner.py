import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from common import collect_text_snippets, object_to_dict, save_json
from config import MAX_OUTPUT_TOKENS
from output_parser import parse_generation_output

load_dotenv()
client = OpenAI()


def extract_text_from_openai_response(response) -> str:
    if hasattr(response, "output_text"):
        text = getattr(response, "output_text")
        if text:
            return text.strip()

    snippets = collect_text_snippets(response)
    if snippets:
        return "\n".join(snippets).strip()

    return ""


def call_openai_once(
    case: dict,
    model: str,
    full_prompt: str,
    run_name: str,
    raw_dir: Path,
    parsed_dir: Path,
    failed_dir: Path,
    reasoning: dict | None = None,
) -> dict:
    sample_id = case["id"]
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    raw_path = raw_dir / run_name / f"{sample_id}__{timestamp}.json"
    parsed_path = parsed_dir / run_name / f"{sample_id}__{timestamp}.json"
    failed_path = failed_dir / run_name / f"{sample_id}__{timestamp}.json"

    try:
        request_kwargs = {
            "model": model,
            "input": full_prompt,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "store": False,
        }
        if reasoning is not None:
            request_kwargs["reasoning"] = reasoning

        response = client.responses.create(**request_kwargs)
        response_dict = object_to_dict(response)
        raw_text = extract_text_from_openai_response(response)

        save_json(
            raw_path,
            {
                "provider": "openai",
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
        usage = response_dict.get("usage", {})

        save_json(
            parsed_path,
            {
                "provider": "openai",
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
            "provider": "openai",
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
                "provider": "openai",
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
            "provider": "openai",
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "status": "failed",
            "error": str(e),
            "failed_path": str(failed_path),
        }


def call_openai_with_retry(
    case: dict,
    model: str,
    full_prompt: str,
    run_name: str,
    raw_dir: Path,
    parsed_dir: Path,
    failed_dir: Path,
    max_retries: int = 3,
    reasoning: dict | None = None,
) -> dict:
    last_result = None

    for attempt in range(max_retries):
        result = call_openai_once(
            case=case,
            model=model,
            full_prompt=full_prompt,
            run_name=run_name,
            raw_dir=raw_dir,
            parsed_dir=parsed_dir,
            failed_dir=failed_dir,
            reasoning=reasoning,
        )
        last_result = result

        if result["status"] == "success":
            return result

        time.sleep(2 * (attempt + 1))

    return last_result