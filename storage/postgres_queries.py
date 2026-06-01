from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from config.postgres_config import DB_CONFIG  # noqa: E402


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def _row_to_dict(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}
    return dict(row)


def _rows_to_dicts(rows: List[Any]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


def get_recipe_by_id(recipe_id: int) -> Dict[str, Any]:
    query = """
        SELECT
            r.recipe_id,
            r.title,
            r.source_url,
            r.cuisine,
            r.prep_time_minutes,
            r.servings,
            r.ingredients_json,
            r.steps_json,
            r.raw_json,
            r.scraped_at,
            r.normalized_at,
            r.accepted,
            s.source_name,
            s.source_type,
            s.base_url
        FROM recipes r
        LEFT JOIN sources s ON r.source_id = s.source_id
        WHERE r.recipe_id = %s
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (recipe_id,))
            row = cur.fetchone()

            if row is None:
                return {}

            cur.execute(
                """
                SELECT i.ingredient_name
                FROM recipe_ingredients ri
                JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
                WHERE ri.recipe_id = %s
                ORDER BY i.ingredient_name
                """,
                (recipe_id,),
            )
            ingredients = [r["ingredient_name"] for r in cur.fetchall()]

    result = dict(row)
    result["linked_ingredients"] = ingredients
    return result


def get_recipes_by_cuisine(cuisine: str, limit: int = 20) -> List[Dict[str, Any]]:
    query = """
        SELECT
            recipe_id,
            title,
            source_url,
            cuisine,
            prep_time_minutes,
            servings,
            scraped_at,
            normalized_at
        FROM recipes
        WHERE LOWER(cuisine) = LOWER(%s)
        ORDER BY recipe_id DESC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (cuisine, limit))
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def get_recipes_by_ingredient(
    ingredient_name: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    query = """
        SELECT DISTINCT
            r.recipe_id,
            r.title,
            r.source_url,
            r.cuisine,
            r.prep_time_minutes,
            r.servings
        FROM recipes r
        JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
        WHERE LOWER(i.ingredient_name) LIKE LOWER(%s)
        ORDER BY r.recipe_id DESC
        LIMIT %s
    """

    pattern = f"%{ingredient_name}%"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (pattern, limit))
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def get_recipes_by_source(source_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    query = """
        SELECT
            r.recipe_id,
            r.title,
            r.source_url,
            r.cuisine,
            r.prep_time_minutes,
            r.servings,
            s.source_name
        FROM recipes r
        LEFT JOIN sources s ON r.source_id = s.source_id
        WHERE LOWER(s.source_name) = LOWER(%s)
        ORDER BY r.recipe_id DESC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (source_name, limit))
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def search_recipes_by_title(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    query = """
        SELECT
            recipe_id,
            title,
            source_url,
            cuisine,
            prep_time_minutes,
            servings
        FROM recipes
        WHERE LOWER(title) LIKE LOWER(%s)
        ORDER BY recipe_id DESC
        LIMIT %s
    """

    pattern = f"%{keyword}%"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (pattern, limit))
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def get_top_ingredients(limit: int = 20) -> List[Dict[str, Any]]:
    query = """
        SELECT
            i.ingredient_name,
            COUNT(*) AS usage_count
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
        GROUP BY i.ingredient_name
        ORDER BY usage_count DESC, i.ingredient_name ASC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def get_cuisine_counts() -> List[Dict[str, Any]]:
    query = """
        SELECT
            COALESCE(cuisine, 'Unknown') AS cuisine,
            COUNT(*) AS recipe_count
        FROM recipes
        GROUP BY COALESCE(cuisine, 'Unknown')
        ORDER BY recipe_count DESC, cuisine ASC
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def get_source_counts() -> List[Dict[str, Any]]:
    query = """
        SELECT
            s.source_name,
            COUNT(r.recipe_id) AS recipe_count
        FROM sources s
        LEFT JOIN recipes r ON s.source_id = r.source_id
        GROUP BY s.source_name
        ORDER BY recipe_count DESC, s.source_name ASC
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

    return _rows_to_dicts(rows)


def print_recipe(recipe: Dict[str, Any]) -> None:
    if not recipe:
        print("No recipe found.")
        return

    print("\n" + "=" * 60)
    print(f"Recipe ID   : {recipe.get('recipe_id')}")
    print(f"Title       : {recipe.get('title')}")
    print(f"Source      : {recipe.get('source_name')}")
    print(f"URL         : {recipe.get('source_url')}")
    print(f"Cuisine     : {recipe.get('cuisine')}")
    print(f"Prep Time   : {recipe.get('prep_time_minutes')}")
    print(f"Servings    : {recipe.get('servings')}")
    print(f"Accepted    : {recipe.get('accepted')}")
    print("\nIngredients:")
    for item in recipe.get("linked_ingredients", []):
        print(f"  - {item}")
    print("=" * 60 + "\n")


def main() -> None:
    print("\nDATABASE CHECK")
    print("=" * 40)

    cuisine_counts = get_cuisine_counts()
    print("\nCuisine Counts:")
    for row in cuisine_counts:
        print(f"{row['cuisine']:<20} {row['recipe_count']}")

    top_ingredients = get_top_ingredients(10)
    print("\nTop Ingredients:")
    for row in top_ingredients:
        print(f"{row['ingredient_name']:<30} {row['usage_count']}")

    print("\nSample Recipe By Cuisine: Indian")
    recipes = get_recipes_by_cuisine("Indian", limit=3)
    for recipe in recipes:
        print(recipe)

    print("\nSearch by title keyword: paneer")
    matches = search_recipes_by_title("paneer", limit=3)
    for match in matches:
        print(match)


if __name__ == "__main__":
    main()