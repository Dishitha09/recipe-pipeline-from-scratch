from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from crawl.filter_recipe_urls import is_probably_recipe_url


def load_records(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Records file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data and isinstance(data["records"], list):
        return data["records"]

    raise ValueError("records file must contain a JSON list or a dict with a 'records' list")


def is_valid_recipe_record(record: Dict[str, Any]) -> bool:
    raw = record.get("raw_content", {})
    if not isinstance(raw, dict):
        return False

    title = str(raw.get("title", "")).strip()
    source_url = str(raw.get("source_url", "")).strip()
    ingredients = raw.get("ingredients", [])
    steps = raw.get("steps", [])

    if not title or title.lower().startswith("untitled"):
        return False

    if not source_url or not is_probably_recipe_url(source_url):
        return False

    if not isinstance(ingredients, list) or not isinstance(steps, list):
        return False

    if len(ingredients) < 3:
        return False

    if len(steps) < 3:
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate crawled recipe records.")
    parser.add_argument("--input", required=True, help="Path to records.json")
    parser.add_argument("--clean-output", default="records_clean.json", help="Path to save accepted records")
    parser.add_argument("--rejected-output", default="records_rejected.json", help="Path to save rejected records")
    args = parser.parse_args()

    input_path = Path(args.input)
    clean_output = Path(args.clean_output)
    rejected_output = Path(args.rejected_output)

    records = load_records(input_path)

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for record in records:
        if is_valid_recipe_record(record):
            accepted.append(record)
        else:
            rejected.append(record)

    clean_output.write_text(json.dumps(accepted, indent=2, ensure_ascii=False), encoding="utf-8")
    rejected_output.write_text(json.dumps(rejected, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nVALIDATION REPORT")
    print("=" * 60)
    print(f"Input records   : {len(records)}")
    print(f"Accepted        : {len(accepted)}")
    print(f"Rejected        : {len(rejected)}")
    print(f"Accepted output : {clean_output}")
    print(f"Rejected output : {rejected_output}")
    print("=" * 60)


if __name__ == "__main__":
    main()