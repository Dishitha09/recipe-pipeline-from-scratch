import pandas as pd

FILE = "data/master_ingredients_final_v3.csv"

df = pd.read_csv(FILE)

print("\nTOTAL ROWS\n")
print(len(df))

print("\nNON-ASCII CANONICALS\n")

non_ascii = df[
    df["canonical_name"]
    .astype(str)
    .str.contains(
        r"[^ -~]",
        regex=True,
        na=False,
    )
]

print(len(non_ascii))

print(
    non_ascii[
        ["canonical_name"]
    ]
    .head(100)
    .to_string()
)

print("\nPOSSIBLE QUANTITY PHRASES\n")

quantity_words = [
    "cup",
    "cups",
    "tsp",
    "tbsp",
    "teaspoon",
    "tablespoon",
    "pinch",
]

bad = df[
    df["canonical_name"]
    .astype(str)
    .str.contains(
        "|".join(quantity_words),
        case=False,
        na=False,
    )
]

print(len(bad))

print(
    bad[
        ["canonical_name"]
    ]
    .head(100)
    .to_string()
)