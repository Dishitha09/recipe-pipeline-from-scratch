from typing import Dict, Any


UNIT_ALIASES = {
    "cups": "cup",
    "c": "cup",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "t.": "tsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp.": "tbsp",
    "oz": "g",
    "ounce": "g",
    "ounces": "g",
    "lb": "g",
    "pound": "g",
    "pounds": "g",
    "gms": "g",
    "gram": "g",
    "grams": "g",
    "mls": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
}

COLLOQUIAL_UNITS = {
    "handful": ("g", 30.0),
    "pinch": ("g", 0.3),
    "a pinch": ("g", 0.3),
    "to taste": ("g", None),
    "as needed": ("g", None),
    "squeeze": ("ml", 5.0),
}


def harmonise_unit(quantity: Any, unit: str) -> Dict[str, Any]:
    raw_unit = (unit or "").strip().lower()

    if raw_unit in COLLOQUIAL_UNITS:
        canonical_unit, estimated_value = COLLOQUIAL_UNITS[raw_unit]
        return {
            "quantity_value": estimated_value if estimated_value is not None else None,
            "normalized_unit": canonical_unit,
            "flag": "colloquial_unit",
        }

    canonical_unit = UNIT_ALIASES.get(raw_unit, raw_unit)

    if canonical_unit in {"g", "ml", "tsp", "tbsp", "cup", "count"}:
        try:
            quantity_value = float(quantity)
        except (TypeError, ValueError):
            quantity_value = None

        return {
            "quantity_value": quantity_value,
            "normalized_unit": canonical_unit,
            "flag": None,
        }

    return {
        "quantity_value": quantity,
        "normalized_unit": None,
        "flag": "unknown_unit",
    }