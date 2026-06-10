import pandas as pd

FILE = "data/master_ingredients_final_v4.csv"

df = pd.read_csv(FILE)

ALIAS_UPDATES = {

    "turmeric": [
        "haldi",
        "haldi powder",
        "turmeric powder",
    ],

    "atta": [
        "gehun atta",
        "whole wheat flour",
        "wheat flour",
    ],

    "cilantro leaves": [
        "coriander leaves",
        "coriander leaf",
        "cilantro",
    ],

    "ghee": [
        "clarified butter",
    ],

    "yogurt": [
        "curd",
        "dahi",
        "plain yogurt",
    ],
}


for canonical, aliases in ALIAS_UPDATES.items():

    mask = (
        df["canonical_name"]
        .astype(str)
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

    alias_set = {
        x.strip()
        for x in existing.split("|")
        if x.strip()
    }

    for alias in aliases:
        alias_set.add(alias)

    df.loc[idx, "aliases"] = "|".join(
        sorted(alias_set)
    )

df.to_csv(
    FILE,
    index=False,
)

print("Alias repair complete")