import json
from collections import Counter

from enrichment.ingredient_parser import parse_ingredient

units = Counter()

with open(
    "data/final_recipes.json",
    "r",
    encoding="utf-8",
) as f:

    recipes = json.load(f)

for recipe in recipes:

    ingredients = (
        recipe.get(
            "raw_content",
            {}
        ).get(
            "ingredients",
            []
        )
    )

    for ingredient in ingredients:

        parsed = parse_ingredient(
            ingredient
        )

        unit = parsed.get(
            "unit"
        )

        if unit:
            units[unit.lower()] += 1

print(
    "\nTOP UNITS\n"
)

for unit, count in units.most_common(50):

    print(
        unit,
        count,
    )