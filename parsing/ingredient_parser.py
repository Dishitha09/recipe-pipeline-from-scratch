from __future__ import annotations

import re
from typing import Any, Dict, Optional, List


UNIT_ALIASES = {
    "cup": "cup",
    "cups": "cup",
    "c": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsps": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsps": "tsp",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "ml": "ml",
    "liter": "l",
    "litre": "l",
    "l": "l",
    "oz": "oz",
    "lb": "lb",
    "pinch": "pinch",
    "handful": "handful",
    "slice": "slice",
    "slices": "slice",
    "piece": "piece",
    "pieces": "piece",
    "cube": "count",
    "cubes": "count",
    "clove": "count",
    "cloves": "count",
    "sprig": "count",
    "sprigs": "count",
    "leaf": "count",
    "leaves": "count",
    "stalk": "count",
    "stalks": "count",
    "count": "count",
}

QUANTITY_PATTERN = re.compile(
    r"^\s*(?P<qty>\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+|a|an)\s+"
    r"(?:(?P<unit>[A-Za-z]+)\s+)?(?P<name>.*)$",
    re.IGNORECASE,
)

FRACTION_PATTERN = re.compile(r"^(?P<whole>\d+)\s+(?P<num>\d+)/(?P<den>\d+)$")
SIMPLE_FRACTION_PATTERN = re.compile(r"^(?P<num>\d+)/(?P<den>\d+)$")


def parse_quantity(value: str) -> Optional[float]:
    text = value.strip().lower()

    if text in {"a", "an"}:
        return 1.0

    match = FRACTION_PATTERN.match(text)
    if match:
        whole = float(match.group("whole"))
        num = float(match.group("num"))
        den = float(match.group("den"))
        if den != 0:
            return whole + (num / den)

    match = SIMPLE_FRACTION_PATTERN.match(text)
    if match:
        num = float(match.group("num"))
        den = float(match.group("den"))
        if den != 0:
            return num / den

    try:
        return float(text)
    except ValueError:
        return None


def normalize_unit(unit: Optional[str]) -> Optional[str]:
    if not unit:
        return None

    cleaned = unit.strip().lower().rstrip(".")
    return UNIT_ALIASES.get(cleaned, cleaned)


def clean_ingredient_name(text: str) -> str:
    text = re.sub(r"\([^)]*\)", "", text)  # remove parenthetical notes
    text = text.strip()
    text = re.sub(r"^(of\s+)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,.-")


def parse_ingredient_text(text: Any) -> Dict[str, Any]:
    raw = str(text).strip()

    if not raw:
        return {
            "raw_text": raw,
            "quantity": None,
            "unit": None,
            "ingredient": None,
            "flag": "empty_ingredient",
        }

    lowered = raw.lower()

    if lowered.endswith(" to taste"):
        ingredient = raw[: -len(" to taste")].strip()
        return {
            "raw_text": raw,
            "quantity": None,
            "unit": None,
            "ingredient": clean_ingredient_name(ingredient),
            "flag": "to_taste",
        }

    if lowered.startswith(("a pinch of ", "pinch of ")):
        ingredient = raw.split("of", 1)[1].strip() if "of" in raw.lower() else raw
        return {
            "raw_text": raw,
            "quantity": None,
            "unit": "pinch",
            "ingredient": clean_ingredient_name(ingredient),
            "flag": "colloquial_unit",
        }

    if lowered.startswith(("a handful of ", "handful of ")):
        ingredient = raw.split("of", 1)[1].strip() if "of" in raw.lower() else raw
        return {
            "raw_text": raw,
            "quantity": None,
            "unit": "handful",
            "ingredient": clean_ingredient_name(ingredient),
            "flag": "colloquial_unit",
        }

    match = QUANTITY_PATTERN.match(raw)
    if not match:
        return {
            "raw_text": raw,
            "quantity": None,
            "unit": None,
            "ingredient": clean_ingredient_name(raw),
            "flag": "unparsed_ingredient",
        }

    qty_text = match.group("qty")
    unit_text = match.group("unit")
    name_text = match.group("name") or ""

    quantity = parse_quantity(qty_text)
    unit = normalize_unit(unit_text)
    ingredient_name = clean_ingredient_name(name_text)

    if quantity is None and qty_text.lower() in {"a", "an"}:
        quantity = 1.0

    if not ingredient_name and unit_text:
        ingredient_name = unit_text.strip()

    flag = None
    if unit in {"pinch", "handful"}:
        flag = "colloquial_unit"
    elif unit is None and quantity is not None:
        flag = "missing_unit"
    elif quantity is None:
        flag = "missing_quantity"

    return {
        "raw_text": raw,
        "quantity": quantity,
        "unit": unit,
        "ingredient": ingredient_name,
        "flag": flag,
    }


def parse_ingredient_list(items: list[Any]) -> list[Dict[str, Any]]:
    return [parse_ingredient_text(item) for item in items]