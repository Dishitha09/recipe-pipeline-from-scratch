import pandas as pd

FILE = "data/master_ingredients_final_v2.csv"

df = pd.read_csv(FILE)

ALIAS_MAP = {

    "cumin": [
        "jeera",
        "jeera powder",
        "cumin powder",
        "cumin seeds",
        "shahi jeera",
    ],

    "turmeric": [
        "haldi",
        "haldi powder",
        "turmeric powder",
    ],

    "coriander leaves": [
        "cilantro",
        "cilantro leaves",
        "coriander leaf",
        "coriander",
        "coriander leaves",
    ],

    "yogurt": [
        "curd",
        "plain yogurt",
        "dahi",
    ],

    "all purpose flour": [
        "maida",
    ],

    "whole wheat flour": [
        "atta",
        "gehun atta",
        "wheat flour",
    ],

    "hing": [
        "asafoetida",
        "a pinch hing",
        "pinch asafoetida",
    ],

    "red chili powder": [
        "red chilli powder",
        "kashmiri red chili powder",
        "kashmiri red chilli powder",
        "chilli powder",
    ],

    "green chili": [
        "green chilli",
        "green chilies",
    ],

    "garlic": [
        "garlic cloves",
        "garlic paste",
    ],

    "ginger": [
        "ginger paste",
        "grated ginger",
    ],

    "tomato": [
        "tomatoes",
        "tomatoes",
    ],

    "paneer": [
        "cottage cheese",
    ],

    "besan": [
        "gram flour",
        "chickpea flour",
    ],

    "ghee": [
        "clarified butter",
    ],

    "mustard seeds": [
        "rai",
        "sarson",
    ],

    "fennel seeds": [
        "saunf",
    ],

    "cardamom": [
        "elaichi",
    ],

    "cinnamon": [
        "dalchini",
    ],

    "clove": [
        "lavang",
    ],
}


for canonical, aliases in ALIAS_MAP.items():

    mask = (
        df["canonical_name"]
        .str.lower()
        .eq(canonical.lower())
    )

    if not mask.any():
        continue

    idx = df[mask].index[0]

    existing = str(
        df.loc[idx, "aliases"]
    )

    if existing == "nan":
        existing = ""

    existing_set = {
        x.strip()
        for x in existing.split("|")
        if x.strip()
    }

    for alias in aliases:
        existing_set.add(alias)

    df.loc[idx, "aliases"] = "|".join(
        sorted(existing_set)
    )

df.to_csv(
    FILE,
    index=False,
)

print(
    "Alias expansion complete"
)

print(
    f"Rows: {len(df)}"
)