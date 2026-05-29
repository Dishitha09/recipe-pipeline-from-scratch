from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pipeline_runner import run_pipeline


SOURCE_FILE = Path("data/raw/hebbars_kitchen_recipes.json")
PIPELINE_INPUT_FILE = Path("data/raw/web_recipes.json")
NORMALIZER_SCRIPT = Path("normalization/recipe_normalizer.py")
INGREDIENT_CATALOG_SCRIPT = Path("processed_data/ingredient_catalog.py")
CUISINE_CLASSIFIER_SCRIPT = Path("processed_data/cuisine_classifier.py")
SNAPSHOT_SCRIPT = Path("tracking/run_snapshot.py")


def load_recipes() -> list:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SOURCE_FILE}")

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "recipes" in data and isinstance(data["recipes"], list):
        return data["recipes"]

    raise ValueError("Unexpected JSON structure")


def write_pipeline_input(recipes: list) -> None:
    PIPELINE_INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PIPELINE_INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"recipes": recipes}, f, ensure_ascii=False, indent=2)


def run_script(script_path: Path, label: str) -> None:
    if not script_path.exists():
        print(f"{label} not found: {script_path}")
        return

    print(f"\nRunning {label}...")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"{label} failed with exit code {result.returncode}")


def run_snapshot() -> None:
    run_script(SNAPSHOT_SCRIPT, "run snapshot")


def main() -> None:
    recipes = load_recipes()
    print(f"Loaded {len(recipes)} recipes")

    write_pipeline_input(recipes)

    summary = run_pipeline()

    print("\nPipeline summary:")
    print(summary)

    run_script(NORMALIZER_SCRIPT, "recipe normalizer")
    run_script(INGREDIENT_CATALOG_SCRIPT, "ingredient catalog")
    run_script(CUISINE_CLASSIFIER_SCRIPT, "cuisine classifier")

    print("\nCreating run snapshot...")
    run_snapshot()


if __name__ == "__main__":
    main()