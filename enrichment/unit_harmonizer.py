import re


CANONICAL_UNITS = {
    "g",
    "ml",
    "tsp",
    "tbsp",
    "cup",
    "count",
}


UNIT_ALIASES = {

"gram": "g",
"grams": "g",
"kg": "g",

"clove": "count",
"cloves": "count",

"piece": "count",
"pieces": "count",

"inch": "count",

    "gram": "g",
    "grams": "g",
    "gm": "g",
    "gms": "g",
    "g": "g",

    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "ml": "ml",

    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "t.": "tsp",

    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",

    "cup": "cup",
    "cups": "cup",
    "c": "cup",
    "cupful": "cup",
    "cup-ful": "cup",

    "piece": "count",
    "pieces": "count",
    "clove": "count",
    "cloves": "count",
    "onion": "count",
    "onions": "count",
}


COLLOQUIAL_UNITS = {
    "handful": {
        "qty": 30,
        "unit": "g",
    },
    "pinch": {
        "qty": 0.3,
        "unit": "g",
    },
    "dash": {
        "qty": 0.5,
        "unit": "g",
    },
    "squeeze": {
        "qty": 5,
        "unit": "ml",
    },
}


BLOCKED_UNITS = {
    "oz",
    "ounce",
    "ounces",
    "lb",
    "lbs",
    "pound",
    "pounds",
    "fl_oz",
}


def harmonize(
    quantity,
    raw_unit,
):

    result = {
        "quantity": quantity,
        "unit": raw_unit,
        "canonical_unit": None,
        "conversion_factor": 1.0,
        "flag": None,
    }

    if raw_unit is None:

        result["canonical_unit"] = "count"

        return result

    unit = str(raw_unit).lower().strip()

    unit = re.sub(
        r"\s+",
        " ",
        unit,
    )

    if unit in COLLOQUIAL_UNITS:

        result["quantity"] = (
            COLLOQUIAL_UNITS[unit]["qty"]
        )

        result["canonical_unit"] = (
            COLLOQUIAL_UNITS[unit]["unit"]
        )

        result["flag"] = (
            "colloquial_unit"
        )

        return result

    if unit in BLOCKED_UNITS:

        result["flag"] = (
            "uom_conflict"
        )

        return result

    if unit in UNIT_ALIASES:

        result["canonical_unit"] = (
            UNIT_ALIASES[unit]
        )

        return result

    result["flag"] = (
        "unknown_unit"
    )

    return result


if __name__ == "__main__":

    tests = [
        ("1", "cups"),
        ("2", "teaspoon"),
        ("3", "tbsp"),
        ("1", "handful"),
        ("1", "pinch"),
        ("10", "oz"),
        ("2", "cloves"),
    ]

    for qty, unit in tests:

        print(
            harmonize(
                qty,
                unit,
            )
        )