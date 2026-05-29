from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


RAW_INPUT_PATH = Path("data/raw/hebbars_kitchen_recipes.json")
OUTPUT_PATH = Path("processed_data/normalized_recipes.json")


CUISINE_TAGS = {
    "south indian": "South Indian",
    "north indian": "North Indian",
    "punjabi": "Punjabi",
    "gujarati": "Gujarati",
    "rajasthani": "Rajasthani",
    "bengali": "Bengali",
    "maharashtrian": "Maharashtrian",
    "tamil": "Tamil",
    "kerala": "Kerala",
    "andhra": "Andhra",
    "karnataka": "Karnataka",
    "indian": "Indian",
}


def load_raw_recipes() -> List[Dict[str, Any]]:
    if not RAW_INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {RAW_INPUT_PATH}")

    with open(RAW_INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "recipes" in data and isinstance(data["recipes"], list):
        return data["recipes"]

    raise ValueError("Unexpected raw recipe JSON format")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_title(title: Any) -> str:
    text = clean_text(title)
    text = re.sub(r"\s*\|\s*hebbars kitchen.*$", "", text, flags=re.I)
    return text.strip(" -|")


def normalize_servings(servings: Any) -> Optional[int]:
    if servings is None:
        return None

    if isinstance(servings, int):
        return servings

    if isinstance(servings, float):
        return int(servings)

    text = clean_text(servings).lower()

    match = re.search(r"\d+", text)
    if match:
        return int(match.group())

    return None


def normalize_prep_time(prep_time: Any) -> Optional[int]:
    if prep_time is None:
        return None

    if isinstance(prep_time, int):
        return prep_time

    text = clean_text(prep_time).upper()

    if text.isdigit():
        return int(text)

    total_minutes = 0

    hours_match = re.search(r"PT(\d+)H", text)
    minutes_match = re.search(r"PT(?:\d+H)?(\d+)M", text)

    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60

    if minutes_match:
        total_minutes += int(minutes_match.group(1))

    if total_minutes > 0:
        return total_minutes

    numbers = re.findall(r"\d+", text)
    if numbers:
        return int(numbers[0])

    return None


def normalize_ingredients(ingredients: Any) -> List[str]:
    if not ingredients:
        return []

    normalized: List[str] = []

    for item in ingredients:
        if isinstance(item, str):
            text = clean_text(item)
        elif isinstance(item, dict):
            text = clean_text(
                item.get("raw_text")
                or item.get("ingredient")
                or item.get("name")
                or ""
            )
        else:
            text = clean_text(item)

        if text:
            normalized.append(text)

    return normalized


def normalize_steps(steps: Any) -> List[str]:
    if not steps:
        return []

    normalized: List[str] = []

    for step in steps:
        text = clean_text(step)
        if text:
            normalized.append(text)

    return normalized


def extract_cuisine_tags(raw_cuisine: Any) -> List[str]:
    cuisines: List[str] = []

    if isinstance(raw_cuisine, list):
        cuisines = [clean_text(x).lower() for x in raw_cuisine if clean_text(x)]
    elif raw_cuisine:
        cuisines = [clean_text(raw_cuisine).lower()]

    tags: List[str] = []

    for cuisine in cuisines:
        for key, tag in CUISINE_TAGS.items():
            if key in cuisine:
                tags.append(tag)

    if not tags and cuisines:
        tags.append("Indian")

    return sorted(set(tags))


def extract_tags(recipe: Dict[str, Any]) -> List[str]:
    tags = set()

    title = clean_title(recipe.get("title", ""))
    cuisine = recipe.get("cuisine")
    category = recipe.get("recipe_category", [])

    if title:
        words = title.lower().split()
        for word in words:
            if len(word) > 2:
                tags.add(word.strip(",.!?"))

    tags.update(extract_cuisine_tags(cuisine))

    if isinstance(category, list):
        for item in category:
            text = clean_text(item)
            if text:
                tags.add(text)

    return sorted(tags)


def generate_recipe_id(recipe: Dict[str, Any]) -> str:
    key = f"{clean_title(recipe.get('title', ''))}|{clean_text(recipe.get('source_url', ''))}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def normalize_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_title(recipe.get("title"))
    ingredients = normalize_ingredients(recipe.get("ingredients", []))
    steps = normalize_steps(recipe.get("steps", []))

    normalized = {
        "recipe_id": generate_recipe_id(recipe),
        "title": title,
        "source_name": clean_text(recipe.get("source_name")),
        "source_url": clean_text(recipe.get("source_url")),
        "cuisine": recipe.get("cuisine"),
        "cuisine_tags": extract_cuisine_tags(recipe.get("cuisine")),
        "prep_time_minutes": normalize_prep_time(recipe.get("prep_time")),
        "servings": normalize_servings(recipe.get("servings")),
        "ingredients": ingredients,
        "steps": steps,
        "tags": extract_tags(recipe),
        "raw_json_ld": recipe.get("raw_json_ld"),
    }

    return normalized


def main() -> None:
    recipes = load_raw_recipes()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    normalized_recipes = [normalize_recipe(recipe) for recipe in recipes]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized_recipes, f, indent=2, ensure_ascii=False)

    print(f"Loaded {len(recipes)} raw recipes")
    print(f"Saved {len(normalized_recipes)} normalized recipes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()