from enrichment.unit_converter import (
    convert_to_grams
)

result = convert_to_grams(
    quantity=1,
    unit="cup",
    ingredient_name="water",
)

assert (
    round(
        result[
            "quantity_g"
        ],
        0
    )
    == 240
)

print(
    "Density tests passed"
)