from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


INPUT_FILE = Path("processed_data/normalized_recipes.json")
OUTPUT_FILE = Path("processed_data/normalized_recipes_clean.json")


UNIT_WORDS = (
    "cup", "cups", "tbsp", "tbsps", "tablespoon", "tablespoons",
    "tsp", "tsps", "teaspoon", "teaspoons",
    "g", "gram", "grams", "kg", "kilogram", "kilograms",
    "ml", "milliliter", "milliliters", "l", "liter", "liters", "litre", "litres",
    "pinch", "pinches", "handful", "handfuls", "piece", "pieces",
    "slice", "slices", "clove", "cloves", "can", "cans",
    "packet", "packets", "bowl", "bowls", "stick", "sticks",
    "sprig", "sprigs", "leaf", "leaves"
)

FRACTION_MAP = {
    "½": "1/2",
    "¼": "1/4",
    "¾": "3/4",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}

DESCRIPTORS = (
    "a few",
    "few",
    "some",
    "several",
    "a handful of",
    "handful of",
    "small",
    "large",
    "medium",
    "to taste",
    "as needed",
    "optional",
    "fresh",
    "finely chopped",
    "roughly chopped",
    "chopped",
    "sliced",
    "grated",
    "crushed",
    "minced",
    "ground",
    "powder",
)


def load_recipes() -> List[Dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("normalized_recipes.json must contain a JSON list")

    return data


def remove_hindi_and_kannada(text: str) -> str:
    return re.sub(r"[\u0900-\u097F\u0C80-\u0CFF]+", " ", text)


def clean_ingredient(text: Any) -> str:
    if text is None:
        return ""

    value = str(text).strip().lower()
    value = value.replace("Â", "").replace("Ã", "")

    for k, v in FRACTION_MAP.items():
        value = value.replace(k, f" {v} ")

    value = remove_hindi_and_kannada(value)

    # Remove bracketed notes
    value = re.sub(r"\((.*?)\)", "", value, flags=re.I)

    # Remove common leading descriptors
    descriptor_pattern = r"|".join(re.escape(d) for d in sorted(DESCRIPTORS, key=len, reverse=True))
    value = re.sub(rf"^\s*(?:{descriptor_pattern})\s+", "", value, flags=re.I)

    # Normalize spaces around slash fractions like "/ 2" -> "/2"
    value = re.sub(r"/\s+(\d+)", r"/\1", value)

    # Remove leading quantities:
    # 1, 1.5, 1/2, /2, 1 1/2, 2-3, 2 to 3
    value = re.sub(
        r"^\s*(?:\d+\s+\d+/\d+|\d+\s*/\s*\d+|/\d+|\d+/\d+|\d+\.\d+|\d+\s*-\s*\d+|\d+\s*to\s*\d+|\d+)\s*",
        "",
        value,
        flags=re.I,
    )

    unit_pattern = r"|".join(re.escape(u) for u in UNIT_WORDS)

    # Remove unit words at the start
    value = re.sub(rf"^\s*({unit_pattern})\b\.?\s*", "", value, flags=re.I)

    # Remove any leftover fraction at the start
    value = re.sub(r"^\s*/?\d+\s*/\s*\d+\s*", "", value)

    # Remove unit words again after fraction cleanup
    value = re.sub(rf"^\s*({unit_pattern})\b\.?\s*", "", value, flags=re.I)

    # Remove repeated leftover quantity + unit combos at the front
    value = re.sub(
        r"^\s*(?:\d+\s+\d+/\d+|\d+\s*/\s*\d+|/\d+|\d+/\d+|\d+\.\d+|\d+)\s+",
        "",
        value,
        flags=re.I,
    )

    value = remove_hindi_and_kannada(value)

    # Keep only readable characters
    value = re.sub(r"[^\x00-\x7F]+", " ", value)
    value = re.sub(r"[^\w\s\-/()']", "", value)
    value = re.sub(r"\s+", " ", value).strip(" -.,;:()[]{}")

    return value


def clean_ingredients_list(ingredients: Any) -> List[str]:
    if not isinstance(ingredients, list):
        return []

    cleaned: List[str] = []

    for item in ingredients:
        text = clean_ingredient(item)
        if text and re.search(r"[A-Za-z]", text):
            cleaned.append(text)

    return cleaned


def main() -> None:
    recipes = load_recipes()
    cleaned_recipes: List[Dict[str, Any]] = []

    for recipe in recipes:
        new_recipe = dict(recipe)
        new_recipe["ingredients"] = clean_ingredients_list(recipe.get("ingredients", []))
        cleaned_recipes.append(new_recipe)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_recipes, f, ensure_ascii=False, indent=2)

    print(f"Loaded recipes          : {len(recipes)}")
    print(f"Saved cleaned recipes   : {len(cleaned_recipes)}")
    print(f"Output file             : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()