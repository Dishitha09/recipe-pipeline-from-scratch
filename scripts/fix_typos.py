import pandas as pd

FILE = "data/master_ingredients_final_v2.csv"

TYPO_MAP = {
    "jeea": "cumin",
    "to mato": "tomato",
    "to matoes": "tomato",
    "corainder powder": "coriander powder",
}

df = pd.read_csv(FILE)

df["canonical_name"] = (
    df["canonical_name"]
    .replace(TYPO_MAP)
)

df = (
    df.groupby(
        "canonical_name",
        as_index=False,
    )
    .first()
)

df.to_csv(
    FILE,
    index=False,
)

print(
    f"Rows after cleanup: {len(df)}"
)