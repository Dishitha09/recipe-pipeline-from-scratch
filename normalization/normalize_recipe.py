from typing import Dict, Any, List


def normalize_ingredient_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "raw_name": row.get("raw_name"),
        "canonical_name": row.get("canonical_name"),
        "resolution_type": row.get("resolution_type"),
        "quantity": row.get("quantity"),
        "unit": row.get("unit"),
        "quantity_value": row.get("quantity_value"),
        "normalized_unit": row.get("normalized_unit"),
        "flag": row.get("flag"),
    }


def normalize_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    source_ingredients = recipe.get("ingredients_enriched", recipe.get("ingredients", []))

    normalized_ingredients: List[Dict[str, Any]] = []

    for item in source_ingredients:
        if isinstance(item, dict):
            normalized_ingredients.append(normalize_ingredient_row(item))
        else:
            normalized_ingredients.append(
                {
                    "raw_name": str(item),
                    "canonical_name": None,
                    "resolution_type": "unstructured",
                    "quantity": None,
                    "unit": None,
                    "quantity_value": None,
                    "normalized_unit": None,
                    "flag": "unstructured_ingredient",
                }
            )

    return {
        **recipe,
        "ingredients_normalized": normalized_ingredients,
    }