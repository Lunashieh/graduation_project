import argparse
import json
import re
from datetime import datetime
from pathlib import Path

RESULT_RE = re.compile(r"^RESULT\s+(.*?)\s+is\s+(true|false)\.\s*$")

def parse_proverif_log(log_path: Path):
    queries = []
    violated = []
    if not log_path.exists():
        raise FileNotFoundError(f"Missing log file: {log_path}")

    text = log_path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        m = RESULT_RE.match(line.strip())
        if not m:
            continue
        qtext = m.group(1).strip()
        ok = (m.group(2) == "true")
        queries.append({"text": qtext, "result": ok})
        if not ok:
            violated.append(qtext)

    return queries, violated

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True, help="Protocol family name, e.g., NeedhamSchroederPK")
    ap.add_argument("--variant", required=True, help="Variant name, e.g., baseline / BIND_01")
    ap.add_argument("--dir", required=True, help="Directory that contains model.pv and proverif.log")
    ap.add_argument("--command", default="proverif -in pitype model.pv", help="Command used to run ProVerif")
    args = ap.parse_args()

    d = Path(args.dir)
    log_path = d / "proverif.log"
    model_path = d / "model.pv"

    out_path = d / "verdict.json"

    queries, violated = parse_proverif_log(log_path)

    verdict = {
        "protocol_family": args.protocol,
        "variant": args.variant,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "proverif": {
            "command": args.command,
            "all_ok": (len(queries) > 0 and len(violated) == 0),
            "queries": queries,
            "violated": violated
        },
        "artifacts": {
            "model": str(model_path.name) if model_path.exists() else None,
            "log": str(log_path.name),
    
        }
    }

    out_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()