from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from config.postgres_config import DB_CONFIG


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def print_header(title: str):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def main():

    conn = get_connection()
    cur = conn.cursor()

    # =====================================================
    # TOTALS
    # =====================================================

    cur.execute("SELECT COUNT(*) FROM recipes")
    total_recipes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ingredients")
    total_ingredients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM recipe_ingredients")
    total_links = cur.fetchone()[0]

    # =====================================================
    # TOP CUISINES
    # =====================================================

    cur.execute("""
        SELECT cuisine,
               COUNT(*) AS recipe_count
        FROM recipes
        WHERE cuisine IS NOT NULL
        GROUP BY cuisine
        ORDER BY recipe_count DESC
        LIMIT 10
    """)

    top_cuisines = cur.fetchall()

    # =====================================================
    # TOP INGREDIENTS
    # =====================================================

    cur.execute("""
        SELECT i.ingredient_name,
               COUNT(*) AS frequency
        FROM recipe_ingredients ri
        JOIN ingredients i
            ON ri.ingredient_id = i.ingredient_id
        GROUP BY i.ingredient_name
        ORDER BY frequency DESC
        LIMIT 15
    """)

    top_ingredients = cur.fetchall()

    # =====================================================
    # AVG INGREDIENTS PER RECIPE
    # =====================================================

    cur.execute("""
        SELECT ROUND(
            AVG(ingredient_count),
            1
        )
        FROM (
            SELECT recipe_id,
                   COUNT(*) AS ingredient_count
            FROM recipe_ingredients
            GROUP BY recipe_id
        ) x
    """)

    avg_ingredients = cur.fetchone()[0]

    # =====================================================
    # AVG PREP TIME
    # =====================================================

    cur.execute("""
        SELECT ROUND(
            AVG(prep_time_minutes),
            1
        )
        FROM recipes
        WHERE prep_time_minutes IS NOT NULL
    """)

    avg_prep_time = cur.fetchone()[0]

    # =====================================================
    # REPORT
    # =====================================================

    print_header("RECIPE ANALYTICS REPORT")

    print(f"\nTotal Recipes      : {total_recipes}")
    print(f"Total Ingredients  : {total_ingredients}")
    print(f"Ingredient Links   : {total_links}")

    print("\nTop Cuisines")
    print("-" * 25)

    for cuisine, count in top_cuisines:
        print(f"{str(cuisine):20} {count}")

    print("\nTop Ingredients")
    print("-" * 25)

    for ingredient, count in top_ingredients:
        print(f"{ingredient:20} {count}")

    print("\nAverage Ingredients Per Recipe")
    print("-" * 35)
    print(avg_ingredients)

    print("\nAverage Prep Time")
    print("-" * 20)
    print(f"{avg_prep_time} mins")

    print("\n" + "=" * 50)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()