from enrichment.ingredient_resolver import resolve_ingredient

tests = ["atta", "tomato", "paneer", "mystery spice"]

for item in tests:
    print(resolve_ingredient(item))