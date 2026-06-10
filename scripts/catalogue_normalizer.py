import pandas as pd

INPUT_FILE = "data/master_ingredients_final.csv"
OUTPUT_FILE = "data/master_ingredients_final_v2.csv"

REPLACEMENTS = {

    "ginger paste or freshly grated or crushed": "ginger",
    "ginger paste": "ginger",

    "garlic paste or freshly grated": "garlic",

    "plain yogurt )": "yogurt",

    "water as required": "water",
    "water to knead": "water",

    "oil for roasting": "oil",

    "pinch of salt": "salt",
    "pinch salt": "salt",

    "a pinch hing": "hing",
    "pinch asafoetida": "hing",

    "red onion )": "red onion",

    "liter whole milk": "milk",
    "litre milk": "milk",

    "half lemon": "lemon",
    "juice of 1": "lemon juice",

    "ball sized tamarind": "tamarind",
}


df = pd.read_csv(INPUT_FILE)

df["canonical_name"] = (
    df["canonical_name"]
    .replace(REPLACEMENTS)
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
    f"Saved: {OUTPUT_FILE}"
)

print(
    f"Rows: {len(df)}"
)