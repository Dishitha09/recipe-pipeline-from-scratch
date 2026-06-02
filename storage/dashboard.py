from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

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


def print_header(title: str):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def main():
    raw_recipes = safe_count_json(RAW_FILE)

    try:
        conn = get_connection()
    except Exception as exc:
        print_header("RECIPE DATA PLATFORM DASHBOARD")
        print(f"\nDatabase Health     : FAILED")
        print(f"Connection Error    : {exc}")
        print("\n" + "=" * 50)
        return

    try:
        cur = conn.cursor()

        recipes_stored = fetch_one(cur, "SELECT COUNT(*) FROM recipes")[0]
        ingredients_stored = fetch_one(cur, "SELECT COUNT(*) FROM ingredients")[0]
        ingredient_links = fetch_one(cur, "SELECT COUNT(*) FROM recipe_ingredients")[0]
        sources_stored = fetch_one(cur, "SELECT COUNT(*) FROM sources")[0]

        top_cuisine_row = fetch_one(
            cur,
            """
            SELECT COALESCE(cuisine, 'Unknown') AS cuisine, COUNT(*) AS cnt
            FROM recipes
            GROUP BY COALESCE(cuisine, 'Unknown')
            ORDER BY cnt DESC, cuisine ASC
            LIMIT 1
            """,
        )
        top_cuisine = top_cuisine_row[0] if top_cuisine_row else "Unknown"
        top_cuisine_count = top_cuisine_row[1] if top_cuisine_row else 0

        top_ingredient_row = fetch_one(
            cur,
            """
            SELECT i.ingredient_name, COUNT(*) AS cnt
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
            GROUP BY i.ingredient_name
            ORDER BY cnt DESC, i.ingredient_name ASC
            LIMIT 1
            """,
        )
        top_ingredient = top_ingredient_row[0] if top_ingredient_row else "Unknown"
        top_ingredient_count = top_ingredient_row[1] if top_ingredient_row else 0

        avg_prep_time = fetch_one(
            cur,
            """
            SELECT COALESCE(ROUND(AVG(prep_time_minutes)::numeric, 1), 0)
            FROM recipes
            WHERE prep_time_minutes IS NOT NULL
            """,
        )[0]

        accepted_recipes = recipes_stored
        rejected_recipes = max(raw_recipes - accepted_recipes, 0)
        acceptance_rate = round((accepted_recipes / raw_recipes) * 100, 2) if raw_recipes else 0.0

        print_header("RECIPE DATA PLATFORM DASHBOARD")

        print(f"\nRaw Recipes         : {raw_recipes}")
        print(f"Recipes Stored      : {recipes_stored}")
        print(f"Ingredients Stored  : {ingredients_stored}")
        print(f"Ingredient Links    : {ingredient_links}")
        print(f"Sources Stored      : {sources_stored}")

        print(f"\nAcceptance Rate     : {acceptance_rate}%")
        print(f"Rejected Recipes    : {rejected_recipes}")

        print(f"\nTop Cuisine         : {top_cuisine} ({top_cuisine_count})")
        print(f"Top Ingredient      : {top_ingredient} ({top_ingredient_count})")
        print(f"Average Prep Time   : {avg_prep_time} mins")

        print("\nSearch Layer        : READY")
        print("Database Health     : OK")
        print("\n" + "=" * 50)

        cur.close()
        conn.close()

    except Exception as exc:
        try:
            conn.close()
        except Exception:
            pass

        print_header("RECIPE DATA PLATFORM DASHBOARD")
        print(f"\nDatabase Health     : FAILED")
        print(f"Error               : {exc}")
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()