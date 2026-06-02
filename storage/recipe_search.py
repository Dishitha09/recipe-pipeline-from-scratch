from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from config.postgres_config import DB_CONFIG  # noqa: E402


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_rows(query: str, params: tuple[Any, ...]) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def search_recipes(
    term: Optional[str] = None,
    cuisine: Optional[str] = None,
    ingredient: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    where_clauses: List[str] = []
    params: List[Any] = []

    base_query = """
        SELECT DISTINCT
            r.recipe_id,
            r.title,
            r.cuisine,
            r.prep_time_minutes,
            r.servings,
            r.source_url
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
        LEFT JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
    """

    if term:
        where_clauses.append(
            """(
                r.title ILIKE %s
                OR r.cuisine ILIKE %s
                OR i.ingredient_name ILIKE %s
            )"""
        )
        like_term = f"%{term}%"
        params.extend([like_term, like_term, like_term])

    if cuisine:
        where_clauses.append("r.cuisine ILIKE %s")
        params.append(f"%{cuisine}%")

    if ingredient:
        where_clauses.append("i.ingredient_name ILIKE %s")
        params.append(f"%{ingredient}%")

    if where_clauses:
        base_query += "\nWHERE " + "\n  AND ".join(where_clauses)

    base_query += """
        ORDER BY r.recipe_id DESC
        LIMIT %s
    """
    params.append(limit)

    return fetch_rows(base_query, tuple(params))


def print_results(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("No matching recipes found.")
        return

    print("\n" + "=" * 70)
    print(f"FOUND {len(rows)} RECIPES")
    print("=" * 70)

    for row in rows:
        print(f"ID      : {row.get('recipe_id')}")
        print(f"Title   : {row.get('title')}")
        print(f"Cuisine : {row.get('cuisine')}")
        print(f"Prep    : {row.get('prep_time_minutes')} mins")
        print(f"Servings: {row.get('servings')}")
        print(f"URL     : {row.get('source_url')}")
        print("-" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search recipes stored in PostgreSQL."
    )
    parser.add_argument(
        "term",
        nargs="?",
        default=None,
        help="Search term for title/cuisine/ingredient",
    )
    parser.add_argument(
        "--cuisine",
        default=None,
        help="Filter by cuisine",
    )
    parser.add_argument(
        "--ingredient",
        default=None,
        help="Filter by ingredient name",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results",
    )

    args = parser.parse_args()

    rows = search_recipes(
        term=args.term,
        cuisine=args.cuisine,
        ingredient=args.ingredient,
        limit=args.limit,
    )

    print_results(rows)


if __name__ == "__main__":
    main()