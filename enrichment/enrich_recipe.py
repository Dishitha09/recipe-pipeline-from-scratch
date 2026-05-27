from typing import Dict, Any, List

from enrichment.ingredient_resolver import resolve_ingredient


def enrich_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    enriched_ingredients: List[Dict[str, Any]] = []
    unresolved_ingredients: List[str] = []

    ingredients = recipe.get("ingredients", [])

    for ingredient in ingredients:
        raw_name = None

        if isinstance(ingredient, dict):
            raw_name = (
                ingredient.get("ingredient")
                or ingredient.get("name")
                or ingredient.get("raw_name")
                or ingredient.get("raw_text")
            )
        else:
            raw_name = str(ingredient)

        result = resolve_ingredient(raw_name or "")
        result["raw_name"] = raw_name

        if isinstance(ingredient, dict):
            result["quantity"] = ingredient.get("quantity")
            result["unit"] = ingredient.get("unit")
            result["flag"] = ingredient.get("flag")
        else:
            result["quantity"] = None
            result["unit"] = None
            result["flag"] = None

        enriched_ingredients.append(result)

        if result["resolution_type"] == "unresolved":
            unresolved_ingredients.append(raw_name or "")

    exact_matches = sum(
        1 for item in enriched_ingredients if item["resolution_type"] == "exact"
    )
    total = len(enriched_ingredients)
    confidence = exact_matches / total if total else 0.0

    return {
        **recipe,
        "ingredients_enriched": enriched_ingredients,
        "unresolved_ingredients": unresolved_ingredients,
        "metadata": {
            **recipe.get("metadata", {}),
            "enrichment_confidence": confidence,
        },
    }