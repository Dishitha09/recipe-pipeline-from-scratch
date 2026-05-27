from typing import Dict, Any, List

from preprocessing.schema import PreProcessedRecipe
from enrichment.ingredient_resolver import resolve_ingredient


def enrich_recipe(recipe: PreProcessedRecipe) -> Dict[str, Any]:
    enriched_ingredients: List[Dict[str, Any]] = []
    unresolved_ingredients: List[str] = []

    for ingredient in recipe.ingredients:
        result = resolve_ingredient(ingredient)
        enriched_ingredients.append(result)

        if result["resolution_type"] == "unresolved":
            unresolved_ingredients.append(ingredient)

    exact_matches = sum(
        1 for item in enriched_ingredients if item["resolution_type"] == "exact"
    )
    total = len(enriched_ingredients)
    confidence = exact_matches / total if total else 0.0

    return {
        "title": recipe.title,
        "cuisine": recipe.cuisine,
        "prep_time": recipe.prep_time,
        "servings": recipe.servings,
        "steps": recipe.steps,
        "ingredients_enriched": enriched_ingredients,
        "unresolved_ingredients": unresolved_ingredients,
        "metadata": {
            **recipe.metadata,
            "enrichment_confidence": confidence,
        },
    }