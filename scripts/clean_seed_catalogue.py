import pandas as pd
import re

INPUT_FILE = "data/master_ingredients_seed.csv"
OUTPUT_FILE = "data/master_ingredients_clean.csv"

df = pd.read_csv(INPUT_FILE)

BAD_PATTERNS = [
    r"^\d+",
    r"^\+",
    r"&amp;",
    r"\bcup\b",
    r"\bcups\b",
    r"\btablespoon\b",
    r"\btablespoons\b",
    r"\bteaspoon\b",
    r"\bteaspoons\b",
    r"\bclove\b",
    r"\bcloves\b",
    r"\bwater\b$",
]

mask = pd.Series(False, index=df.index)

for pattern in BAD_PATTERNS:
    mask |= df["canonical_name"].astype(str).str.contains(
        pattern,
        case=False,
        regex=True,
        na=False,
    )

bad_rows = df[mask]
good_rows = df[~mask]

print("Bad rows:", len(bad_rows))
print("Good rows:", len(good_rows))

good_rows.to_csv(
    OUTPUT_FILE,
    index=False,
)

print("Saved:", OUTPUT_FILE)