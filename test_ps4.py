from normalization.normalize_recipe import normalize_recipe


sample_recipe = {
    "title": "Demo Recipe",
    "ingredients": [
        {"name": "flour", "quantity": 1, "unit": "cups"},
        {"name": "spinach", "quantity": "a handful", "unit": "handful"},
        {"name": "salt", "quantity": "a pinch", "unit": "pinch"},
        {"name": "water", "quantity": 2, "unit": "liters"},
    ],
}

normalized = normalize_recipe(sample_recipe)

print(normalized)

assert normalized["ingredients_normalized"][0]["normalized_unit"] == "cup"
assert normalized["ingredients_normalized"][1]["normalized_unit"] == "g"
assert normalized["ingredients_normalized"][1]["flag"] == "colloquial_unit"
assert normalized["ingredients_normalized"][2]["normalized_unit"] == "g"
assert normalized["ingredients_normalized"][2]["flag"] == "colloquial_unit"

print("PS-4 test passed")