from enrichment.unit_harmonizer import (
    harmonize,
)

from enrichment.unit_converter import (
    convert_to_grams,
    convert_from_grams,
)

from enrichment.density_table import (
    get_density,
)

print("\nPS-4 ACCEPTANCE TEST\n")

# R4.1

tests = [
    ("1", "cups"),
    ("1", "teaspoon"),
    ("1", "tbsp"),
    ("1", "cloves"),
]

canonical_ok = True

for qty, unit in tests:

    result = harmonize(
        qty,
        unit,
    )

    print(result)

    if result["canonical_unit"] not in {
        "g",
        "ml",
        "tsp",
        "tbsp",
        "cup",
        "count",
    }:
        canonical_ok = False

print(
    "\nR4.1:",
    "PASS" if canonical_ok else "FAIL",
)

# R4.3

conflict = harmonize(
    "10",
    "oz",
)

print(
    "\nR4.3:",
    conflict["flag"],
)

# R4.4

colloquial = harmonize(
    "1",
    "handful",
)

print(
    "\nR4.4:",
    colloquial,
)

# R4.2

density = get_density(
    "ginger"
)

print(
    "\nR4.2:",
    density,
)

# R4.5

result = convert_to_grams(
    "water",
    1,
    "cup",
)

reverse = convert_from_grams(
    "water",
    result["quantity_g"],
    "cup",
)

print(
    "\nR4.5:",
    result,
    reverse,
)

print(
    "\nPS-4 COMPLETE\n"
)
