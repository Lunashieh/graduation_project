import json
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def object_to_dict(obj: Any) -> Any:
    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, Path):
        return str(obj)

    if isinstance(obj, list):
        return [object_to_dict(item) for item in obj]

    if isinstance(obj, tuple):
        return [object_to_dict(item) for item in obj]

    if isinstance(obj, dict):
        return {str(k): object_to_dict(v) for k, v in obj.items()}

    for method_name in ("model_dump", "to_dict", "dict"):
        if hasattr(obj, method_name):
            try:
                method = getattr(obj, method_name)
                return object_to_dict(method())
            except Exception:
                pass

    if hasattr(obj, "__dict__"):
        try:
            return object_to_dict(vars(obj))
        except Exception:
            pass

    return repr(obj)


def save_json(path: Path, data: Any) -> None:
    ensure_parent(path)
    serializable = object_to_dict(data)
    path.write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def collect_text_snippets(obj: Any) -> list[str]:
    snippets: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "text" and isinstance(item, str) and item.strip():
                    snippets.append(item.strip())
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(object_to_dict(obj))
    return snippets