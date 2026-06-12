import pandas as pd
import re

CATALOGUE_FILE = (
    "data/master_ingredients_final_v4.csv"
)

df = pd.read_csv(
    CATALOGUE_FILE
)

print("\nDATA QA REPORT\n")

# Duplicate canonicals
duplicates = df[
    df.duplicated(
        subset=["canonical_name"],
        keep=False,
    )
]

print(
    f"Duplicate canonicals: {len(duplicates)}"
)

# Quantity phrases
quantity_pattern = re.compile(
    r"(pinch|cup|tbsp|tsp|gram|kg|ml)",
    re.I,
)

quantity_rows = df[
    df["canonical_name"]
    .astype(str)
    .str.contains(
        quantity_pattern,
        regex=True,
        na=False,
    )
]

print(
    f"Possible quantity phrases: {len(quantity_rows)}"
)

# Non-ascii
non_ascii = df[
    df["canonical_name"]
    .astype(str)
    .apply(
        lambda x:
        not x.isascii()
    )
]

print(
    f"Non ASCII names: {len(non_ascii)}"
)

# Missing IDs
missing_ids = df[
    df["ingredient_id"]
    .isna()
]

print(
    f"Missing IDs: {len(missing_ids)}"
)

print(
    "\nQA COMPLETE"
)