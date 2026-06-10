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

    # Weight
    "kg": "g",
    "gram": "g",
    "grams": "g",
    "gm": "g",
    "gms": "g",
    "g": "g",

    # Volume
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "ml": "ml",

    # Teaspoon
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "t.": "tsp",

    # Tablespoon
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",

    # Cup
    "cup": "cup",
    "cups": "cup",
    "c": "cup",
    "cupful": "cup",
    "cup-ful": "cup",

    # Count
    "piece": "count",
    "pieces": "count",
    "clove": "count",
    "cloves": "count",
    "onion": "count",
    "onions": "count",
    "inch": "count",
}


SCALE_FACTORS = {
    "kg": 1000,
    "gram": 1,
    "grams": 1,
    "gm": 1,
    "gms": 1,
    "g": 1,
}


COLLOQUIAL_UNITS = {

    "handful": {
        "qty": 30,
        "unit": "g",
    },

    "mutthi": {
        "qty": 40,
        "unit": "g",
    },

    "pinch": {
        "qty": 0.3,
        "unit": "g",
    },

    "chutki": {
        "qty": 0.5,
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

    "katori": {
        "qty": 150,
        "unit": "ml",
    },

    "pav": {
        "qty": 250,
        "unit": "g",
    },

    "seer": {
        "qty": 933,
        "unit": "g",
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

        try:

            qty = float(quantity)

            if unit in SCALE_FACTORS:

                qty = (
                    qty
                    * SCALE_FACTORS[unit]
                )

                result["quantity"] = qty

        except Exception:
            pass

        return result

    result["flag"] = (
        "unknown_unit"
    )

    return result


if __name__ == "__main__":

    tests = [
        ("1", "kg"),
        ("1", "cups"),
        ("2", "teaspoon"),
        ("3", "tbsp"),
        ("1", "handful"),
        ("1", "mutthi"),
        ("1", "katori"),
        ("1", "chutki"),
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