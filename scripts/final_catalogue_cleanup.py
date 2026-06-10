import pandas as pd
import re

INPUT_FILE = "data/master_ingredients_final_v3.csv"
OUTPUT_FILE = "data/master_ingredients_final_v4.csv"

df = pd.read_csv(INPUT_FILE)

REPLACEMENTS = {

    "काजू": "cashew",
    "गाजर": "carrot",
    "टमाटर": "tomato",
    "प्याज": "onion",
    "मिर्च": "chili",
    "लौंग": "clove",
    "सेब": "apple",
    "तेल": "oil",
    "पानी": "water",
    "हरी मिर्च": "green chili",
    "बे पत्ती": "bay leaf",
    "बे लीफ": "bay leaf",

    "pinch turmeric": "turmeric",
    "pinch sugar": "sugar",
    "pinch saffron": "saffron",
    "pinch cumin powder": "cumin powder",
    "pinch coriander powder": "coriander powder",
    "pinch garam masala": "garam masala",
    "pinch black pepper": "black pepper",

    "a pinch sugar": "sugar",
    "a pinch baking soda": "baking soda",
    "a pinch baking powder": "baking powder",
}

df["canonical_name"] = (
    df["canonical_name"]
    .astype(str)
    .str.strip()
)

df["canonical_name"] = (
    df["canonical_name"]
    .replace(REPLACEMENTS)
)

# Remove quantity/unit prefixes

df["canonical_name"] = (
    df["canonical_name"]
    .str.replace(
        r"^(a\s+pinch\s+of\s+)",
        "",
        regex=True,
    )
)

df["canonical_name"] = (
    df["canonical_name"]
    .str.replace(
        r"^(pinch\s+of\s+)",
        "",
        regex=True,
    )
)

df["canonical_name"] = (
    df["canonical_name"]
    .str.replace(
        r"^(pinch\s+)",
        "",
        regex=True,
    )
)

df["canonical_name"] = (
    df["canonical_name"]
    .str.replace(
        r"^\d+\/?\d*\s*tsp\s+",
        "",
        regex=True,
    )
)

df = (
    df.groupby(
        "canonical_name",
        as_index=False,
    )
    .first()
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print(
    f"Rows after cleanup: {len(df)}"
)

print(
    f"Saved: {OUTPUT_FILE}"
)