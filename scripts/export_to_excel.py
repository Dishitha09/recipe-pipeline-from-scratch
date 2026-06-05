import json
import pandas as pd

INPUT_FILE = "data/final_recipes.json"
OUTPUT_FILE = "data/recipes.xlsx"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    recipes = json.load(f)

rows = []

for recipe in recipes:
    raw = recipe.get("raw_content", {})

    rows.append(
        {
            "Title": raw.get("title"),
            "Source URL": raw.get("source_url"),
            "Cuisine": raw.get("cuisine"),
            "Prep Time": raw.get("prep_time"),
            "Cook Time": raw.get("cook_time"),
            "Servings": raw.get("servings"),
            "Ingredients": "\n".join(raw.get("ingredients", [])),
            "Steps": "\n".join(raw.get("steps", [])),
        }
    )

df = pd.DataFrame(rows)

df.to_excel(
    OUTPUT_FILE,
    index=False,
    engine="openpyxl"
)

print("=" * 50)
print(f"Recipes exported : {len(df)}")
print(f"Saved to         : {OUTPUT_FILE}")
print("=" * 50)