from pathlib import Path
import json

# Root directory of our modified dataset
ROOT_DIR = Path("data_modified")

# Output JSON file
OUTPUT_JSON = Path("dataset.json")


def read_text_file(file_path: Path) -> str:
    """
    Read a text file safely.
    Try UTF-8 first, then fall back to latin-1.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def build_dataset(root_dir: Path) -> list:
    """
    Build dataset from the following structure:

    data_modified/
        <protocol>/
            baseline/
                model.pv
                proverif.log
                verdict.json
            bugs/
                bug_01/
                    model.pv
                    proverif.log
                    patch.diff
                    verdict.json
                bug_02/
                bug_03/

    Only bug folders are included in the final dataset.
    Baseline folders are ignored.
    """
    if not root_dir.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root_dir}")

    dataset = []

    # Each subdirectory under data_modified is treated as one protocol
    protocol_dirs = sorted([p for p in root_dir.iterdir() if p.is_dir()])

    if not protocol_dirs:
        raise ValueError(f"No protocol folders found under: {root_dir}")

    for protocol_dir in protocol_dirs:
        protocol_name = protocol_dir.name
        bugs_dir = protocol_dir / "bugs"

        # Skip protocol folders without a bugs subfolder
        if not bugs_dir.exists() or not bugs_dir.is_dir():
            print(f"Skip {protocol_name}: no 'bugs' directory found.")
            continue

        # Each subdirectory under bugs is one bug model, e.g. bug_01, bug_02, bug_03
        bug_dirs = sorted([p for p in bugs_dir.iterdir() if p.is_dir()])

        if not bug_dirs:
            print(f"Skip {protocol_name}: no bug folders found in 'bugs'.")
            continue

        for bug_dir in bug_dirs:
            bug_model = bug_dir.name

            pv_file = bug_dir / "model.pv"
            log_file = bug_dir / "proverif.log"

            # Strictly require these two files
            if not pv_file.exists():
                print(f"Skip {protocol_name}/{bug_model}: missing model.pv")
                continue

            if not log_file.exists():
                print(f"Skip {protocol_name}/{bug_model}: missing proverif.log")
                continue

            pv_text = read_text_file(pv_file)
            log_text = read_text_file(log_file)

            record = {
                "id": f"{protocol_name}_{bug_model}",
                "protocol": protocol_name,
                "bug_model": bug_model,
                "pv_text": pv_text,
                "log_text": log_text
            }

            dataset.append(record)
            print(f"Added: {record['id']}")

    return dataset


def main():
    dataset = build_dataset(ROOT_DIR)

    if not dataset:
        raise ValueError("No valid bug records were collected.")

    OUTPUT_JSON.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\nDone. Saved {len(dataset)} records to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()