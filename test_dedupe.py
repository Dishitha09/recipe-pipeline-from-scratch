from deduplication.deduplicate import deduplicate_recipes


recipes = [
    {"title": "Paneer Butter Masala", "ingredients": [{"raw_name": "paneer"}, {"raw_name": "butter"}]},
    {"title": "paneer butter masala", "ingredients": [{"raw_name": "paneer"}, {"raw_name": "butter"}]},
    {"title": "Masala Dosa", "ingredients": [{"raw_name": "rice"}, {"raw_name": "urad dal"}]},
]

unique_recipes, duplicate_recipes = deduplicate_recipes(recipes)

print("unique:", len(unique_recipes))
print("duplicates:", len(duplicate_recipes))

assert len(unique_recipes) == 2
assert len(duplicate_recipes) == 1

print("Deduplication test passed")