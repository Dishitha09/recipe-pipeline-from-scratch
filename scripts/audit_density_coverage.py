import pandas as pd

from enrichment.density_table import (
    get_density,
)

df = pd.read_csv(
    "data/ingredient_candidates.csv"
)

top_200 = df.head(200)

covered = 0

for ingredient in top_200[
    "ingredient_name"
]:

    density = get_density(
        ingredient
    )

    if density:
        covered += 1

print(
    "\nDENSITY COVERAGE REPORT\n"
)

print(
    f"Top 200 Ingredients: {len(top_200)}"
)

print(
    f"Covered: {covered}"
)