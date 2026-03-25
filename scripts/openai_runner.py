import json
import re
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import RAW_DIR, PARSED_DIR, FAILED_DIR, MAX_OUTPUT_TOKENS
from schemas import GenerationOutput

# Load API key from .env
load_dotenv()

# Create OpenAI client
client = OpenAI()


def ensure_parent(path: Path) -> None:
    """
    Ensure the parent folder exists before writing a file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: dict) -> None:
    """
    Save a Python dict as a JSON file.
    """
    ensure_parent(path)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def response_to_dict(response) -> dict:
    """
    Convert the SDK response object to a plain dict if possible.
    """
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    return {"raw_repr": repr(response)}


def extract_text_from_response(response) -> str:
    """
    Best-effort extraction of the model text from the SDK response.
    """
    if hasattr(response, "output_text"):
        text = getattr(response, "output_text")
        if text:
            return text.strip()

    data = response_to_dict(response)
    collected_texts = []

    def walk(obj):
        if isinstance(obj, dict):
            if "text" in obj and isinstance(obj["text"], str):
                collected_texts.append(obj["text"])
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)

    if collected_texts:
        return "\n".join(t.strip() for t in collected_texts if t.strip()).strip()

    return ""


def extract_json_object(text: str) -> str:
    """
    Extract the first JSON object from the model output.
    """
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        json.loads(cleaned)
        return cleaned
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        json.loads(candidate)
        return candidate

    raise ValueError("No valid JSON object found in model output.")


def parse_generation_output(raw_text: str) -> GenerationOutput:
    """
    Parse the raw text into JSON and validate it with Pydantic.
    """
    json_text = extract_json_object(raw_text)
    data = json.loads(json_text)
    return GenerationOutput(**data)


def call_model_once(case: dict, model: str, full_prompt: str, run_name: str) -> dict:
    """
    Call the model once and save both raw and parsed outputs.
    """
    sample_id = case["id"]
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    raw_path = RAW_DIR / run_name / f"{sample_id}__{timestamp}.json"
    parsed_path = PARSED_DIR / run_name / f"{sample_id}__{timestamp}.json"
    failed_path = FAILED_DIR / run_name / f"{sample_id}__{timestamp}.json"

    try:
        response = client.responses.create(
            model=model,
            input=full_prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            store=False,
        )

        response_dict = response_to_dict(response)
        raw_text = extract_text_from_response(response)

        save_json(raw_path, {
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "timestamp": timestamp,
            "prompt": full_prompt,
            "response": response_dict,
            "response_text": raw_text,
        })

        parsed = parse_generation_output(raw_text)
        usage = response_dict.get("usage", {})

        save_json(parsed_path, {
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "timestamp": timestamp,
            "usage": usage,
            "result": parsed.model_dump(),
        })

        return {
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "status": "success",
            "raw_path": str(raw_path),
            "parsed_path": str(parsed_path),
        }

    except Exception as e:
        save_json(failed_path, {
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "timestamp": timestamp,
            "prompt": full_prompt,
            "error": str(e),
        })

        return {
            "sample_id": sample_id,
            "protocol": case["protocol"],
            "bug_id": case["bug_id"],
            "model": model,
            "status": "failed",
            "error": str(e),
            "failed_path": str(failed_path),
        }


def call_model_with_retry(
    case: dict,
    model: str,
    full_prompt: str,
    run_name: str,
    max_retries: int = 3
) -> dict:
    """
    Retry the API call a few times if it fails.
    """
    last_result = None

    for attempt in range(max_retries):
        result = call_model_once(case, model, full_prompt, run_name)
        last_result = result

        if result["status"] == "success":
            return result

        time.sleep(2 * (attempt + 1))

    return last_result