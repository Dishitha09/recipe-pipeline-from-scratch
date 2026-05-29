from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from validation.validator import validate_recipe
from deduplication.dedupe import dedupe_recipes


INPUT_FILE = Path("data/raw/web_recipes.json")
ACCEPTED_FILE = Path("processed_data/accepted_recipes.json")
REJECTED_FILE = Path("quarantine/rejected_recipes.json")


def load_input() -> List[Dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "recipes" in data and isinstance(data["recipes"], list):
        return data["recipes"]

    if isinstance(data, list):
        return data

    raise ValueError("Unexpected input format in web_recipes.json")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_pipeline() -> Dict[str, Any]:
    raw_recipes = load_input()

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for recipe in raw_recipes:
        result = validate_recipe(recipe)

        verdict = result.get("verdict", "REJECTED")

        if verdict == "ACCEPTED":
            accepted.append(recipe)
        else:
            rejected.append(
                {
                    "recipe": recipe,
                    "verdict": verdict,
                    "checks": result.get("check_results", []),
                }
            )

    deduped_accepted, duplicates_removed = dedupe_recipes(accepted)

    write_json(ACCEPTED_FILE, deduped_accepted)
    write_json(REJECTED_FILE, rejected)

    summary = {
        "total": len(raw_recipes),
        "accepted": len(deduped_accepted),
        "rejected": len(rejected),
        "duplicates_removed": duplicates_removed,
    }

    print(f"Pipeline summary: {summary}")
    return summary


if __name__ == "__main__":
    run_pipeline()