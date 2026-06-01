from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import Json

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from config.postgres_config import DB_CONFIG  # noqa: E402


INPUT_FILE = Path("processed_data/normalized_recipes_clean.json")


def load_normalized_recipes() -> List[Dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("normalized_recipes_clean.json must contain a JSON list")

    return data


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def extract_english_title(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    parts = [part.strip() for part in re.split(r"\s*\|\s*", text) if part.strip()]
    if not parts:
        parts = [text]

    candidates: List[str] = []

    for part in parts:
        english_only = re.sub(r"[^\x00-\x7F]+", " ", part)
        english_only = re.sub(r"\s+", " ", english_only).strip(" -/|,.:;")

        if re.search(r"[A-Za-z]", english_only):
            candidates.append(english_only)

    if not candidates:
        english_only = re.sub(r"[^\x00-\x7F]+", " ", text)
        english_only = re.sub(r"\s+", " ", english_only).strip(" -/|,.:;")
        if re.search(r"[A-Za-z]", english_only):
            return english_only
        return None

    def score(s: str) -> int:
        return sum(1 for ch in s if ch.isascii() and ch.isalpha())

    candidates.sort(key=lambda s: (-score(s), len(s)))
    return candidates[0].strip() or None


def normalize_cuisine(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, list):
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        value = cleaned[0] if cleaned else None

    if value is None:
        return None

    text = str(value).strip().lower()
    text = (
        text.replace("{", "")
        .replace("}", "")
        .replace('"', "")
        .replace("'", "")
        .strip()
    )

    if not text:
        return None

    # Remove any non-ASCII text so only English cuisine labels remain
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not re.search(r"[a-z]", text):
        return None

    cuisine_map = {
        "indian": "Indian",
        "indian street food": "Indian Street Food",
"indian street food": "Indian Street Food",
"street food": "Indian Street Food",
        "street food": "Street Food",
        "international": "International",
        "south indian": "South Indian",
        "north indian": "North Indian",
        "indo chinese": "Indo Chinese",
        "bengali": "Bengali",
        "karnataka": "Karnataka",
        "tamil nadu": "Tamil Nadu",
        "mangalore": "Mangalore",
        "andhra": "Andhra",
        "maharashtrian": "Maharashtrian",
        "punjabi": "Punjabi",
        "gujarati": "Gujarati",
        "kerala": "Kerala",
        "rajasthani": "Rajasthani",
        "unknown": None,
    }

    if text in cuisine_map:
        return cuisine_map[text]

    return text.title()


def ensure_source(
    conn,
    source_name: str,
    source_type: str = "web",
    base_url: Optional[str] = None,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sources (source_name, source_type, base_url, status, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (source_name)
            DO UPDATE SET
                source_type = EXCLUDED.source_type,
                base_url = COALESCE(EXCLUDED.base_url, sources.base_url),
                status = EXCLUDED.status
            RETURNING source_id
            """,
            (source_name, source_type, base_url, "completed"),
        )
        source_id = cur.fetchone()[0]

    return source_id


def clean_ingredient_text(text: Any) -> str:
    if text is None:
        return ""

    value = str(text).strip().lower()
    value = value.replace("Â", "").replace("Ã", "")

    value = (
        value.replace("½", " 1/2 ")
        .replace("¼", " 1/4 ")
        .replace("¾", " 3/4 ")
        .replace("⅓", " 1/3 ")
        .replace("⅔", " 2/3 ")
        .replace("⅛", " 1/8 ")
        .replace("⅜", " 3/8 ")
        .replace("⅝", " 5/8 ")
        .replace("⅞", " 7/8 ")
    )

    value = re.sub(r"\((.*?)\)", "", value, flags=re.I)

    # Remove common leading descriptive words
    value = re.sub(
        r"^(?:a\s+few|few|some|several|a\s+handful\s+of|handful\s+of|small|large|medium|to\s+taste|as\s+needed|optional)\s+",
        "",
        value,
        flags=re.I,
    )

    # Remove leading quantity expressions
    value = re.sub(
        r"^\s*(\d+\s+\d+/\d+|\d+\s*/\s*\d+|/\d+|\d+/\d+|\d+\.\d+|\d+\s*-\s*\d+|\d+\s*to\s*\d+|\d+)\s*",
        "",
        value,
        flags=re.I,
    )

    units = (
        "cup", "cups", "tbsp", "tbsps", "tablespoon", "tablespoons",
        "tsp", "tsps", "teaspoon", "teaspoons",
        "g", "gram", "grams", "kg", "kilogram", "kilograms",
        "ml", "milliliter", "milliliters", "l", "liter", "liters", "litre", "litres",
        "pinch", "pinches", "handful", "handfuls", "piece", "pieces",
        "slice", "slices", "clove", "cloves", "can", "cans",
        "packet", "packets", "bowl", "bowls", "stick", "sticks",
        "sprig", "sprigs", "leaf", "leaves",
    )
    unit_pattern = r"|".join(re.escape(u) for u in units)

    value = re.sub(rf"^\s*({unit_pattern})\b\.?\s*", "", value, flags=re.I)
    value = re.sub(r"^\s*/?\d+\s*/\s*\d+\s*", "", value)
    value = re.sub(rf"^\s*({unit_pattern})\b\.?\s*", "", value, flags=re.I)

    # Remove non-English / non-ASCII characters
    value = re.sub(r"[^\x00-\x7F]+", " ", value)

    value = re.sub(r"[^\w\s\-/()']", "", value)
    value = re.sub(r"\s+", " ", value).strip(" -.,;:()[]{}")

    return value


def get_or_create_ingredient(conn, ingredient_name: str) -> Optional[int]:
    ingredient_name = clean_ingredient_text(ingredient_name)
    if not ingredient_name:
        return None

    if not re.search(r"[A-Za-z]", ingredient_name):
        return None

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingredients (ingredient_name)
            VALUES (%s)
            ON CONFLICT (ingredient_name)
            DO UPDATE SET ingredient_name = EXCLUDED.ingredient_name
            RETURNING ingredient_id
            """,
            (ingredient_name,),
        )
        ingredient_id = cur.fetchone()[0]

    return ingredient_id


def upsert_recipe(
    conn,
    recipe: Dict[str, Any],
    source_id: int,
    title: str,
    cuisine: str,
) -> Optional[int]:
    source_url = str(recipe.get("source_url") or "").strip()
    if not source_url:
        return None

    prep_time_minutes = recipe.get("prep_time_minutes")
    servings = recipe.get("servings")
    ingredients = recipe.get("ingredients", [])
    steps = recipe.get("steps", [])
    raw_json_ld = recipe.get("raw_json_ld")
    normalized_at = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO recipes (
                source_id,
                title,
                source_url,
                cuisine,
                prep_time_minutes,
                servings,
                ingredients_json,
                steps_json,
                raw_json,
                scraped_at,
                normalized_at,
                accepted
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, TRUE
            )
            ON CONFLICT (source_url)
            DO UPDATE SET
                source_id = EXCLUDED.source_id,
                title = EXCLUDED.title,
                cuisine = EXCLUDED.cuisine,
                prep_time_minutes = EXCLUDED.prep_time_minutes,
                servings = EXCLUDED.servings,
                ingredients_json = EXCLUDED.ingredients_json,
                steps_json = EXCLUDED.steps_json,
                raw_json = EXCLUDED.raw_json,
                normalized_at = EXCLUDED.normalized_at,
                accepted = EXCLUDED.accepted
            RETURNING recipe_id
            """,
            (
                source_id,
                title,
                source_url,
                cuisine,
                prep_time_minutes,
                servings,
                Json(ingredients),
                Json(steps),
                Json(raw_json_ld),
                normalized_at,
            ),
        )
        recipe_id = cur.fetchone()[0]

    return recipe_id


def link_recipe_ingredients(conn, recipe_id: int, ingredients: List[Any]) -> int:
    linked = 0

    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM recipe_ingredients WHERE recipe_id = %s",
            (recipe_id,),
        )

        for ingredient in ingredients:
            ingredient_id = get_or_create_ingredient(conn, ingredient)
            if ingredient_id is None:
                continue

            cur.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (recipe_id, ingredient_id),
            )
            linked += 1

    return linked


def load_into_postgres() -> Dict[str, Any]:
    recipes = load_normalized_recipes()

    inserted_or_updated = 0
    linked_rows = 0
    skipped_non_english = 0
    skipped_missing_url = 0

    with get_connection() as conn:
        conn.autocommit = False

        for i, recipe in enumerate(recipes, start=1):
            title = extract_english_title(recipe.get("title"))
            cuisine = normalize_cuisine(recipe.get("cuisine"))
            source_url = str(recipe.get("source_url") or "").strip()

            if not title or not cuisine:
                skipped_non_english += 1
                continue

            if not source_url:
                skipped_missing_url += 1
                continue

            parsed = urlparse(source_url)
            base_url = (
                f"{parsed.scheme}://{parsed.netloc}"
                if parsed.scheme and parsed.netloc
                else None
            )

            source_name = recipe.get("source_name") or "Unknown Source"
            source_id = ensure_source(
                conn,
                source_name=source_name,
                source_type="web",
                base_url=base_url,
            )

            recipe_id = upsert_recipe(
                conn,
                recipe,
                source_id=source_id,
                title=title,
                cuisine=cuisine,
            )

            if recipe_id is None:
                skipped_missing_url += 1
                continue

            linked = link_recipe_ingredients(
                conn,
                recipe_id,
                recipe.get("ingredients", []),
            )

            inserted_or_updated += 1
            linked_rows += linked

            if i % 10 == 0:
                print(f"Loaded {i}/{len(recipes)} recipes...")

        conn.commit()

    return {
        "recipes_loaded": inserted_or_updated,
        "ingredient_links_created": linked_rows,
        "skipped_non_english": skipped_non_english,
        "skipped_missing_url": skipped_missing_url,
        "source_file": str(INPUT_FILE),
    }


def main() -> None:
    summary = load_into_postgres()
    print("\nPostgreSQL load complete:")
    print(summary)


if __name__ == "__main__":
    main()