import json
from pathlib import Path

from pipeline_runner import run_pipeline


SOURCE_FILE = Path("data/raw/hebbars_kitchen_recipes.json")
PIPELINE_INPUT_FILE = Path("data/raw/web_recipes.json")


def load_recipes() -> list:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SOURCE_FILE}")

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "recipes" in data:
        return data["recipes"]

    raise ValueError("Unexpected JSON structure")


def main() -> None:
    recipes = load_recipes()

    print(f"Loaded {len(recipes)} recipes")

    PIPELINE_INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PIPELINE_INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"recipes": recipes}, f, ensure_ascii=False, indent=2)

    summary = run_pipeline()

    print("\nPipeline summary:")
    print(summary)


if __name__ == "__main__":
    main()