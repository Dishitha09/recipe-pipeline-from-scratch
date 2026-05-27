from typing import Dict, Any, List, Optional

from preprocessing.schema import PreProcessedRecipe


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


def coerce_raw_record(raw_content: Dict[str, Any]) -> PreProcessedRecipe:
    mapped_keys = {"title", "name", "cuisine", "prep_time", "servings", "ingredients", "steps"}
    unmapped = {k: v for k, v in raw_content.items() if k not in mapped_keys}

    title = first_scalar(raw_content.get("title") or raw_content.get("name"))
    cuisine = first_scalar(raw_content.get("cuisine"))
    prep_time = parse_int(raw_content.get("prep_time") or raw_content.get("totalTime"))
    servings = parse_int(raw_content.get("servings") or raw_content.get("recipeYield"))

    ingredients = split_pipe_field(raw_content.get("ingredients") or raw_content.get("recipeIngredient"))
    steps = split_pipe_field(raw_content.get("steps") or raw_content.get("recipeInstructions"))

    return PreProcessedRecipe(
        title=title,
        cuisine=cuisine,
        prep_time=prep_time,
        servings=servings,
        ingredients=ingredients,
        steps=steps,
        metadata={
            "unmapped": unmapped
        }
    )