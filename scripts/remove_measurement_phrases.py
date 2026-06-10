import pandas as pd
import re

INPUT_FILE = "data/master_ingredients_final_v2.csv"
OUTPUT_FILE = "data/master_ingredients_final_v3.csv"

BAD_PATTERNS = [
    r"^टी स्पून",
    r"^टेबल स्पून",
    r"^स्पून",
    r"^कप",
    r"^½ कप",
    r"^1 कप",
    r"^2 कप",
    r"^3 कप",
    r"^tsp",
    r"^tbsp",
    r"^cup",
    r"^teaspoon",
    r"^tablespoon",
]


def is_bad(name):

    name = str(name).strip()

    for pattern in BAD_PATTERNS:

        if re.search(
            pattern,
            name,
            flags=re.IGNORECASE,
        ):
            return True

    return False


df = pd.read_csv(INPUT_FILE)

before = len(df)

df = df[
    ~df["canonical_name"].apply(is_bad)
]

after = len(df)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print(f"Before: {before}")
print(f"After: {after}")
print(f"Removed: {before - after}")
print(f"Saved: {OUTPUT_FILE}")