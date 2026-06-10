from enrichment.density_table import DENSITY_TABLE


VOLUME_TO_ML = {
    "tsp": 5,
    "tbsp": 15,
    "cup": 240,
}


def convert_to_grams(
    ingredient_name,
    quantity,
    unit,
):

    ingredient_name = (
        str(ingredient_name)
        .lower()
        .strip()
    )

    if unit == "g":

        return {
            "quantity_g": float(quantity),
            "conversion_factor": 1.0,
        }

    if unit not in VOLUME_TO_ML:

        return None

    if ingredient_name not in DENSITY_TABLE:

        return None

    ml = (
        float(quantity)
        * VOLUME_TO_ML[unit]
    )

    density = (
        DENSITY_TABLE
        [ingredient_name]
        ["g_per_ml"]
    )

    grams = ml * density

    return {
        "quantity_g": round(
            grams,
            2,
        ),
        "conversion_factor": density,
    }


def convert_from_grams(
    ingredient_name,
    grams,
    target_unit,
):

    ingredient_name = (
        str(ingredient_name)
        .lower()
        .strip()
    )

    if target_unit not in VOLUME_TO_ML:

        return None

    if ingredient_name not in DENSITY_TABLE:

        return None

    density = (
        DENSITY_TABLE
        [ingredient_name]
        ["g_per_ml"]
    )

    ml = (
        float(grams)
        / density
    )

    quantity = (
        ml
        / VOLUME_TO_ML[target_unit]
    )

    return round(
        quantity,
        4,
    )


if __name__ == "__main__":

    tests = [
        ("water", 1, "cup"),
        ("milk", 1, "cup"),
        ("oil", 1, "cup"),
        ("salt", 1, "tbsp"),
        ("sugar", 1, "tbsp"),
        ("butter", 1, "tbsp"),
        ("yogurt", 1, "cup"),
        ("honey", 1, "tbsp"),
    ]

    print("\nUNIT CONVERSION TESTS\n")

    for ingredient, qty, unit in tests:

        result = convert_to_grams(
            ingredient,
            qty,
            unit,
        )

        print(
            f"INGREDIENT: {ingredient}"
        )

        print(
            f"INPUT: {qty} {unit}"
        )

        print(
            f"GRAMS: {result}"
        )

        if result:

            reverse = convert_from_grams(
                ingredient,
                result["quantity_g"],
                unit,
            )

            print(
                f"ROUND TRIP: {reverse} {unit}"
            )

        print(
            "-" * 50
        )