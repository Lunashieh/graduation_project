import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from common import collect_text_snippets, object_to_dict, save_json
from output_parser import parse_generation_output

load_dotenv()
client = genai.Client()


def extract_text_from_gemini_response(response) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    snippets = collect_text_snippets(response)
    if snippets:
        return "\n".join(snippets).strip()

    return ""


def call_gemini_once(
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
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
        )

        response_dict = object_to_dict(response)
        raw_text = extract_text_from_gemini_response(response)
        usage = object_to_dict(getattr(response, "usage_metadata", None))

        save_json(
            raw_path,
            {
                "provider": "gemini",
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
                "provider": "gemini",
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
            "provider": "gemini",
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
                "provider": "gemini",
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
            "provider": "gemini",
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "status": "failed",
            "error": str(e),
            "failed_path": str(failed_path),
        }


def call_gemini_with_retry(
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
        result = call_gemini_once(
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