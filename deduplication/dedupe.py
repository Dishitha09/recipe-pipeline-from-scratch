from typing import Any, Dict, List, Tuple


def make_recipe_key(recipe: Dict[str, Any]) -> str:
    source_url = str(recipe.get("source_url", "")).strip().lower()
    title = str(recipe.get("title", "")).strip().lower()

    if source_url:
        return source_url

    return title


def dedupe_recipes(
    recipes: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:

    seen = set()
    deduped = []
    duplicates_removed = 0

    for recipe in recipes:
        key = make_recipe_key(recipe)

        if key in seen:
            duplicates_removed += 1
            continue

        seen.add(key)
        deduped.append(recipe)

    return deduped, duplicates_removed