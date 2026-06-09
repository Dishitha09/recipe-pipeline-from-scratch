import json

from enrichment.ingredient_parser import parse_ingredient
from enrichment.ingredient_resolver_v2 import (
    resolve_ingredient_v2,
    get_metrics,
)

TOTAL_INGREDIENT_ROWS = 0

with open(
    "data/final_recipes.json",
    "r",
    encoding="utf-8",
) as f:

    recipes = json.load(f)

for recipe in recipes:

    raw_content = recipe.get(
        "raw_content",
        {}
    )

    ingredients = raw_content.get(
        "ingredients",
        []
    )

    for ingredient in ingredients:

        TOTAL_INGREDIENT_ROWS += 1

        parsed = parse_ingredient(
            ingredient
        )

        ingredient_name = parsed.get(
            "ingredient_name",
            ""
        )

        resolve_ingredient_v2(
            ingredient_name
        )

metrics = get_metrics()

resolved_total = (
    metrics["resolved_exact"]
    + metrics["resolved_vector"]
    + metrics["resolved_llm"]
)

resolution_rate = round(
    (
        resolved_total
        / TOTAL_INGREDIENT_ROWS
    )
    * 100,
    2,
)

llm_usage_rate = round(
    (
        metrics["llm_calls_made"]
        / TOTAL_INGREDIENT_ROWS
    )
    * 100,
    2,
)

print("\nPS-3 ACCEPTANCE REPORT\n")

print(
    f"Ingredient Rows: {TOTAL_INGREDIENT_ROWS}"
)

print(
    f"Resolved Exact: {metrics['resolved_exact']}"
)

print(
    f"Resolved Vector: {metrics['resolved_vector']}"
)

print(
    f"Resolved LLM: {metrics['resolved_llm']}"
)

print(
    f"Unresolved: {metrics['unresolved']}"
)

print(
    f"Resolution Rate: {resolution_rate}%"
)

print(
    f"LLM Calls: {metrics['llm_calls_made']}"
)

print(
    f"LLM Usage Rate: {llm_usage_rate}%"
)

print(
    f"LLM Cost USD: {metrics['llm_cost_usd']}"
)