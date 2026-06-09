import re
from typing import Dict, Any

UNITS = {
    "tsp", "teaspoon", "teaspoons",
    "tbsp", "tablespoon", "tablespoons",
    "cup", "cups",
    "kg", "g", "gram", "grams",
    "ml", "l",
    "inch",
    "clove", "cloves",
    "piece", "pieces",
}

NOISE_PATTERNS = [
    r"\bto taste\b",
    r"\bfor frying\b",
    r"\bfor deep frying\b",
    r"\bfinely chopped\b",
    r"\broughly chopped\b",
    r"\bchopped\b",
    r"\bsmall\b",
    r"\bmedium\b",
    r"\blarge\b",
    r"\bfew\b",
]


def parse_ingredient(raw_text: str) -> Dict[str, Any]:

    text = str(raw_text).lower().strip()

    quantity = None
    unit = None

    text = re.sub(r"\([^)]*\)", "", text)

    match = re.match(
        r"^([\d\/\.¼½¾]+)\s*([a-zA-Z]+)?\s*(.*)$",
        text,
    )

    if match:
        quantity = match.group(1)

        possible_unit = match.group(2)
        remainder = match.group(3)

        if possible_unit and possible_unit.lower() in UNITS:
            unit = possible_unit.lower()
            text = remainder

    text = re.sub(r"^[\d¼½¾\/\.]+\s*", "", text)

    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text)

    if "/" in text:
        parts = [x.strip() for x in text.split("/") if x.strip()]
        if len(parts) >= 2:
            text = parts[0]

    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ,.-")

    return {
        "raw_name": raw_text,
        "quantity": quantity,
        "unit": unit,
        "ingredient_name": text,
    }