
import csv
import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from enrichment.ingredient_parser import parse_ingredient

INPUT_FILE = "data/final_recipes.json"
OUTPUT_FILE = "data/ingredient_candidates.csv"


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    recipes = json.load(f)

counter = Counter()

for recipe in recipes:
    ingredients = recipe.get("raw_content", {}).get("ingredients", [])

    for ingredient in ingredients:
        parsed = parse_ingredient(str(ingredient))

        name = parsed["ingredient_name"].strip().lower()

        if name:
            counter[name] += 1

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow(
        [
            "ingredient_name",
            "count",
        ]
    )

    for ingredient, count in counter.most_common():
        writer.writerow(
            [
                ingredient,
                count,
            ]
        )

print(f"Unique ingredients: {len(counter)}")
print(f"Saved: {OUTPUT_FILE}")
