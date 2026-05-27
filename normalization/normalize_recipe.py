from typing import Dict, Any, List

from normalization.uom_converter import harmonise_unit


def normalize_ingredient_row(row: Dict[str, Any]) -> Dict[str, Any]:
    result = harmonise_unit(row.get("quantity"), row.get("unit"))

    return {
        "name": row.get("name"),
        "quantity": row.get("quantity"),
        "unit": row.get("unit"),
        "quantity_value": result["quantity_value"],
        "normalized_unit": result["normalized_unit"],
        "flag": result["flag"],
    }


def normalize_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    ingredients = recipe.get("ingredients", [])
    normalized_ingredients: List[Dict[str, Any]] = []

    for item in ingredients:
        normalized_ingredients.append(normalize_ingredient_row(item))

    return {
        **recipe,
        "ingredients_normalized": normalized_ingredients,
    }