from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from config.postgres_config import DB_CONFIG  # noqa: E402


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_one(cur, query, params=None):
    cur.execute(query, params or ())
    return cur.fetchone()


def print_header(title: str):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def main():
    conn = get_connection()
    cur = conn.cursor()

    total_recipes = fetch_one(cur, "SELECT COUNT(*) FROM recipes")[0]
    total_ingredients = fetch_one(cur, "SELECT COUNT(*) FROM ingredients")[0]
    total_links = fetch_one(cur, "SELECT COUNT(*) FROM recipe_ingredients")[0]
    total_sources = fetch_one(cur, "SELECT COUNT(*) FROM sources")[0]

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

    cur.close()
    conn.close()

    print_header("RECIPE DATA PLATFORM DASHBOARD")

    print(f"\nRecipes Stored      : {total_recipes}")
    print(f"Ingredients Stored  : {total_ingredients}")
    print(f"Ingredient Links    : {total_links}")
    print(f"Sources Stored      : {total_sources}")

    print(f"\nTop Cuisine         : {top_cuisine} ({top_cuisine_count})")
    print(f"Top Ingredient      : {top_ingredient} ({top_ingredient_count})")
    print(f"Average Prep Time   : {avg_prep_time} mins")

    print("\nDatabase Health     : OK")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()