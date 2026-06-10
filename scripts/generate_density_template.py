import pandas as pd

df = pd.read_csv(
    "data/ingredient_candidates.csv"
)

top_200 = df.head(200)

with open(
    "data/density_candidates.txt",
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "DENSITY_TABLE = {\n"
    )

    for ingredient in top_200[
        "ingredient_name"
    ]:

        ingredient = (
            str(ingredient)
            .lower()
            .strip()
        )

        f.write(
            f'    "{ingredient}": {{"g_per_ml": 1.0}},\n'
        )

    f.write(
        "}\n"
    )

print(
    "Saved: data/density_candidates.txt"
)