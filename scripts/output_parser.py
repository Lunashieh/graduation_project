import json
import re

from schemas import GenerationOutput


def extract_json_object(text: str) -> str:
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
    json_text = extract_json_object(raw_text)
    data = json.loads(json_text)
    return GenerationOutput(**data)