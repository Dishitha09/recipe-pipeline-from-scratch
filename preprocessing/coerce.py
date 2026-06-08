from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from jsonschema import validate

from preprocessing.schema import PreProcessedRecipe


SCHEMA_PATH = Path("config/schema_registry.json")


def load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def split_pipe_field(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        items: List[str] = []
        for x in value:
            text = str(x).strip()
            if text:
                items.append(text)
        return items

    text = str(value).strip()
    if not text:
        return []

    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]

    return [text]


def first_scalar(value: Any) -> Any:
    if isinstance(value, list):
        if not value:
            return None
        return first_scalar(value[0])

    if isinstance(value, dict):
        if "text" in value:
            return first_scalar(value["text"])
        if "value" in value:
            return first_scalar(value["value"])
        return None

    return value


def parse_int(value: Any) -> Optional[int]:
    value = first_scalar(value)

    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    text = str(value).strip()
    if not text:
        return None

    digits = "".join(ch for ch in text if ch.isdigit())

    if digits:
        try:
            return int(digits)
        except ValueError:
            return None

    return None


def validate_recipe(recipe: PreProcessedRecipe) -> None:
    schema = load_schema()

    payload = {
        "title": recipe.title,
        "cuisine": recipe.cuisine,
        "prep_time": recipe.prep_time,
        "servings": recipe.servings,
        "ingredients": recipe.ingredients,
        "steps": recipe.steps,
        "metadata": recipe.metadata,
    }

    validate(instance=payload, schema=schema)


def coerce_raw_record(raw_content: Dict[str, Any]) -> PreProcessedRecipe:
    mapped_keys = {
        "title",
        "name",
        "cuisine",
        "prep_time",
        "servings",
        "ingredients",
        "steps",
        "totalTime",
        "recipeYield",
        "recipeIngredient",
        "recipeInstructions",
    }

    unmapped = {
        k: v
        for k, v in raw_content.items()
        if k not in mapped_keys
    }

    recipe = PreProcessedRecipe(
        title=first_scalar(
            raw_content.get("title")
            or raw_content.get("name")
        ),
        cuisine=first_scalar(
            raw_content.get("cuisine")
        ),
        prep_time=parse_int(
            raw_content.get("prep_time")
            or raw_content.get("totalTime")
        ),
        servings=parse_int(
            raw_content.get("servings")
            or raw_content.get("recipeYield")
        ),
        ingredients=split_pipe_field(
            raw_content.get("ingredients")
            or raw_content.get("recipeIngredient")
        ),
        steps=split_pipe_field(
            raw_content.get("steps")
            or raw_content.get("recipeInstructions")
        ),
        metadata={
            "unmapped": unmapped
        }
    )

    validate_recipe(recipe)

    return recipe