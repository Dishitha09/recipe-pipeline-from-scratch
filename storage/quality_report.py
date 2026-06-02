from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Tuple

import psycopg2

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from config.postgres_config import DB_CONFIG  # noqa: E402


RAW_FILE = Path("processed_data/normalized_recipes_clean.json")


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def safe_count_json(path: Path) -> int:
    if not path.exists():
        return 0

    try:
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return len(data)

        if isinstance(data, dict) and "recipes" in data and isinstance(data["recipes"], list):
            return len(data["recipes"])

    except Exception:
        return 0

    return 0


def fetch_one(cur, query: str, params=None):
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)
    return cur.fetchone()


def fetch_all(cur, query: str, params=None):
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)
    return cur.fetchall()


def grade_quality(acceptance_rate: float, dirty_ratio: float) -> str:
    if acceptance_rate >= 70 and dirty_ratio <= 10:
        return "A"
    if acceptance_rate >= 50 and dirty_ratio <= 20:
        return "B"
    if acceptance_rate >= 30:
        return "C"
    return "D"


def main():
    raw_recipes = safe_count_json(RAW_FILE)

    with get_connection() as conn:
        with conn.cursor() as cur:
            stored_recipes = fetch_one(cur, "SELECT COUNT(*) FROM recipes")[0]
            total_ingredients = fetch_one(cur, "SELECT COUNT(*) FROM ingredients")[0]
            ingredient_links = fetch_one(cur, "SELECT COUNT(*) FROM recipe_ingredients")[0]
            source_count = fetch_one(cur, "SELECT COUNT(*) FROM sources")[0]

            top_cuisines = fetch_all(
                cur,
                """
                SELECT COALESCE(cuisine, 'Unknown') AS cuisine, COUNT(*) AS recipe_count
                FROM recipes
                GROUP BY COALESCE(cuisine, 'Unknown')
                ORDER BY recipe_count DESC, cuisine ASC
                LIMIT 10
                """,
            )

            top_ingredients = fetch_all(
                cur,
                """
                SELECT i.ingredient_name, COUNT(*) AS usage_count
                FROM recipe_ingredients ri
                JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
                GROUP BY i.ingredient_name
                ORDER BY usage_count DESC, i.ingredient_name ASC
                LIMIT 10
                """,
            )

            avg_ingredients_per_recipe = fetch_one(
                cur,
                """
                SELECT COALESCE(ROUND(AVG(ingredient_count)::numeric, 1), 0)
                FROM (
                    SELECT recipe_id, COUNT(*) AS ingredient_count
                    FROM recipe_ingredients
                    GROUP BY recipe_id
                ) x
                """,
            )[0]

            avg_prep_time = fetch_one(
                cur,
                """
                SELECT COALESCE(ROUND(AVG(prep_time_minutes)::numeric, 1), 0)
                FROM recipes
                WHERE prep_time_minutes IS NOT NULL
                """,
            )[0]

            dirty_ingredient_count = fetch_one(
                cur,
                """
                SELECT COUNT(*)
                FROM ingredients
                WHERE ingredient_name ~ '^[0-9/ ]+'
                   OR ingredient_name ILIKE 'few %'
                   OR ingredient_name ILIKE 'some %'
                   OR ingredient_name ILIKE 'a few %'
                   OR ingredient_name ILIKE '%clarified butter%'
                """
            )[0]

    acceptance_rate = round((stored_recipes / raw_recipes) * 100, 2) if raw_recipes else 0.0
    rejected_recipes = max(raw_recipes - stored_recipes, 0)
    dirty_ratio = round((dirty_ingredient_count / total_ingredients) * 100, 2) if total_ingredients else 0.0
    quality_score = grade_quality(acceptance_rate, dirty_ratio)

    print("\n" + "=" * 50)
    print("DATA QUALITY REPORT")
    print("=" * 50)

    print(f"\nRaw Recipes              : {raw_recipes}")
    print(f"Accepted Recipes         : {stored_recipes}")
    print(f"Rejected Recipes         : {rejected_recipes}")
    print(f"Acceptance Rate          : {acceptance_rate}%")
    print(f"Total Ingredients        : {total_ingredients}")
    print(f"Ingredient Links         : {ingredient_links}")
    print(f"Sources Tracked          : {source_count}")
    print(f"Dirty Ingredient Ratio   : {dirty_ratio}%")
    print(f"Quality Score            : {quality_score}")

    print("\nTop Cuisines")
    print("-" * 25)
    for cuisine, count in top_cuisines:
        print(f"{str(cuisine):22} {count}")

    print("\nTop Ingredients")
    print("-" * 25)
    for ingredient_name, usage_count in top_ingredients:
        print(f"{ingredient_name:22} {usage_count}")

    print("\nAverage Ingredients Per Recipe")
    print("-" * 35)
    print(avg_ingredients_per_recipe)

    print("\nAverage Prep Time")
    print("-" * 20)
    print(f"{avg_prep_time} mins")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()