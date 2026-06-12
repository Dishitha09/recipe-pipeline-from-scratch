from enrichment.unit_harmonizer import (
    harmonize
)

assert (
    harmonize(
        1,
        "cups"
    )[
        "canonical_unit"
    ]
    == "cup"
)

assert (
    harmonize(
        1,
        "teaspoon"
    )[
        "canonical_unit"
    ]
    == "tsp"
)

assert (
    harmonize(
        1,
        "cloves"
    )[
        "canonical_unit"
    ]
    == "count"
)

print(
    "Unit tests passed"
)