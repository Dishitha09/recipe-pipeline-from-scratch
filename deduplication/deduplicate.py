from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_ingredient_names(recipe: Dict[str, Any]) -> List[str]:
    ingredients = recipe.get("ingredients_normalized") or recipe.get("ingredients") or []
    names: List[str] = []

    for item in ingredients:
        if isinstance(item, dict):
            name = (
                item.get("canonical_name")
                or item.get("ingredient")
                or item.get("raw_name")
                or item.get("raw_text")
                or item.get("name")
            )
            if name:
                names.append(normalize_text(str(name)))
        else:
            names.append(normalize_text(str(item)))

    return sorted(set(names))


def make_fingerprint(recipe: Dict[str, Any]) -> str:
    title = normalize_text(str(recipe.get("title", "")))
    ingredients = extract_ingredient_names(recipe)
    ingredient_part = "|".join(ingredients)
    return f"{title}::{ingredient_part}"


def deduplicate_recipes(recipes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    seen = set()
    unique_recipes: List[Dict[str, Any]] = []
    duplicate_recipes: List[Dict[str, Any]] = []

    for recipe in recipes:
        fingerprint = make_fingerprint(recipe)

        if fingerprint in seen:
            duplicate_recipes.append(recipe)
        else:
            seen.add(fingerprint)
            unique_recipes.append(recipe)

    return unique_recipes, duplicate_recipes