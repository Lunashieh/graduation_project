import json
from typing import Iterator, List, Dict, Any

from config import DATASET_JSON_PATH


def load_dataset_json() -> List[Dict[str, Any]]:
    """
    Load dataset.json from the project root.

    Supported top-level formats:
    1. A list of records
    2. A dict containing one of:
       - "data"
       - "records"
       - "items"
    """
    if not DATASET_JSON_PATH.exists():
        raise FileNotFoundError(f"dataset.json not found: {DATASET_JSON_PATH}")

    with open(DATASET_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["data", "records", "items"]:
            if key in data and isinstance(data[key], list):
                return data[key]

    raise ValueError(
        "Unsupported dataset.json format. "
        "Expected either a list or a dict containing 'data', 'records', or 'items'."
    )


def normalize_record(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Normalize one raw dataset record into the internal format used by the pipeline.

    Expected raw fields in your current dataset:
    - id
    - protocol
    - bug_model
    - pv_text
    - log_text
    """
    sample_id = str(record.get("id", f"sample_{index:05d}"))
    protocol = str(record.get("protocol", "unknown_protocol"))
    bug_id = str(record.get("bug_model", "unknown_bug"))

    pv_text = record.get("pv_text", "")
    log_text = record.get("log_text", "")

    return {
        "id": sample_id,
        "protocol": protocol,
        "bug_id": bug_id,
        "bug_pv": str(pv_text) if pv_text is not None else "",
        "trace_text": str(log_text) if log_text is not None else "",
        "raw_record": record,
    }


def iter_bug_cases() -> Iterator[Dict[str, Any]]:
    """
    Iterate over normalized records from dataset.json.
    """
    raw_records = load_dataset_json()

    for index, record in enumerate(raw_records):
        yield normalize_record(record, index)