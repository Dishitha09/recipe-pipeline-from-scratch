from validation.validator import validate_recipe


sample_recipe = {
    "title": "Paneer Butter Masala",
    "ingredients": ["paneer", "butter", "tomato"],
    "steps": ["cook", "serve"],
    "metadata": {
        "enrichment_confidence": 0.9
    }
}

result = validate_recipe(sample_recipe)

print(result)

assert result["verdict"] == "ACCEPTED"
print("PS-5 test passed")