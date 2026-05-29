import json
import re
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("processed_data/normalized_recipes.json")
OUTPUT_FILE = Path("processed_data/ingredient_catalog.json")


def clean_ingredient(text):
    if not text:
        return ""

    text = str(text).lower()

    # Fix encoding garbage
    text = text.replace("Â", "")
    text = text.replace("½", "1/2")
    text = text.replace("¼", "1/4")
    text = text.replace("¾", "3/4")

    # Remove anything in brackets
    text = re.sub(r"\(.*?\)", "", text)

    # Remove quantities
    text = re.sub(r"^\d+\s+\d+/\d+\s*", "", text)
    text = re.sub(r"^\d+/\d+\s*", "", text)
    text = re.sub(r"^\d+(\.\d+)?\s*", "", text)

    # Remove common units
    text = re.sub(
        r"^(cup|cups|tsp|tbsp|tablespoon|tablespoons|teaspoon|teaspoons|gram|grams|kg|ml|l|litre|litres|liter|liters|pinch|pinches|clove|cloves|slice|slices|piece|pieces)\s+",
        "",
        text,
    )

    # Remove punctuation
    text = re.sub(r"[^a-zA-Z\s]", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    counter = Counter()

    for recipe in recipes:
        ingredients = recipe.get("ingredients", [])

        for ingredient in ingredients:
            cleaned = clean_ingredient(ingredient)

            if cleaned:
                counter[cleaned] += 1

    catalog = {
        "total_unique_ingredients": len(counter),
        "top_ingredients": [
            {"ingredient": name, "count": count}
            for name, count in counter.most_common()
        ],
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Recipes loaded: {len(recipes)}")
    print(f"Unique ingredients: {len(counter)}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()