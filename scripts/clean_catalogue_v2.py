import re
import pandas as pd


INPUT_FILE = "data/master_ingredients_clean.csv"
OUTPUT_FILE = "data/master_ingredients_final.csv"


BAD_PATTERNS = [

    r"^\d+$",

    r"^\+\s*\d+$",

    r"^&amp;",

    r"^\d+\s+",

    r"cups?\s+water",

    r"garlic\s+cloves?$",

    r"curry\s+leaves?$",

]


def is_bad(name):

    name = str(name).lower().strip()

    if len(name) <= 1:
        return True

    for pattern in BAD_PATTERNS:

        if re.search(
            pattern,
            name,
        ):
            return True

    return False


df = pd.read_csv(
    INPUT_FILE
)

before = len(df)

df = df[
    ~df["canonical_name"]
    .apply(is_bad)
]

after = len(df)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print(
    f"Before: {before}"
)

print(
    f"After: {after}"
)

print(
    f"Removed: {before-after}"
)

print(
    f"Saved: {OUTPUT_FILE}"
)