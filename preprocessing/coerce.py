from typing import Dict, Any, List

from preprocessing.schema import PreProcessedRecipe


def split_pipe_field(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [part.strip() for part in str(value).split("|") if part.strip()]


def coerce_raw_record(raw_content: Dict[str, Any]) -> PreProcessedRecipe:
    mapped_keys = {"title", "cuisine", "prep_time", "servings", "ingredients", "steps"}
    unmapped = {k: v for k, v in raw_content.items() if k not in mapped_keys}

    title = raw_content.get("title") or raw_content.get("name")
    cuisine = raw_content.get("cuisine")
    prep_time = raw_content.get("prep_time")
    servings = raw_content.get("servings")

    if prep_time is not None and prep_time != "":
        try:
            prep_time = int(prep_time)
        except ValueError:
            prep_time = None
    else:
        prep_time = None

    if servings is not None and servings != "":
        try:
            servings = int(servings)
        except ValueError:
            servings = None
    else:
        servings = None

    ingredients = split_pipe_field(raw_content.get("ingredients"))
    steps = split_pipe_field(raw_content.get("steps"))

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