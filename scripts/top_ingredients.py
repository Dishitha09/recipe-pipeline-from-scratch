import pandas as pd

df = pd.read_csv(
    "data/ingredient_candidates.csv"
)

print(
    df.head(200).to_string()
)