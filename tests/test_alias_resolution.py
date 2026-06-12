from enrichment.ingredient_resolver import (
    resolve_ingredient,
)

tests = {

    "haldi powder":
        "turmeric",

    "jeera powder":
        "cumin",

    "gehun atta":
        "atta",

    "curd":
        "yogurt",
}


for query, expected in tests.items():

    result = resolve_ingredient(
        query
    )

    assert (
        result["canonical_name"]
        == expected
    )

print(
    "Alias tests passed"
)