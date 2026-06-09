import csv
from collections import OrderedDict

INPUT_FILE = "data/ingredient_candidates.csv"
OUTPUT_FILE = "data/master_ingredients_seed.csv"


NORMALIZATION_MAP = {
    "green chilli": "green chili",
"green chilies": "green chili",
"chilli": "chili",

"cumin": "cumin",
"cumin seeds": "cumin",
"cumin powder": "cumin",
"jeera": "cumin",

"turmeric powder": "turmeric",

"cilantro": "coriander leaves",
"cilantro or coriander leaves": "coriander leaves",
"coriander": "coriander leaves",

"kashmiri red chilli powder": "red chili powder",
"kashmiri red chili powder": "red chili powder",

"maida": "all purpose flour",

"curd": "yogurt",
"plain yogurt": "yogurt",

"black pepper": "pepper",
"black pepper powder": "pepper",

"mustard": "mustard seeds",

"garlic cloves": "garlic",

"tomatoes": "tomato",
"potatoes": "potato",
"carrots": "carrot",

"cashew": "cashews",

"kasoori methi": "kasuri methi",

"pinch hing": "hing",
"pinch of hing": "hing",

"olive oil": "oil",

"unsalted butter": "butter",

"granulated white sugar": "sugar",
"powdered sugar": "sugar",}


catalogue = OrderedDict()

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        raw_name = row["ingredient_name"].strip().lower()

        canonical = NORMALIZATION_MAP.get(
            raw_name,
            raw_name,
        )

        if canonical not in catalogue:
            catalogue[canonical] = {
                "aliases": set(),
            }

        if raw_name != canonical:
            catalogue[canonical]["aliases"].add(raw_name)

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.writer(f)

    writer.writerow(
        [
            "ingredient_id",
            "canonical_name",
            "aliases",
        ]
    )

    for idx, (canonical, data) in enumerate(
        catalogue.items(),
        start=1,
    ):
        writer.writerow(
            [
                f"ING{idx:04d}",
                canonical,
                "|".join(sorted(data["aliases"])),
            ]
        )

print(f"Canonical ingredients: {len(catalogue)}")
print(f"Saved: {OUTPUT_FILE}")

