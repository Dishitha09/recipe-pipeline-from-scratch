from parsing.ingredient_parser import parse_ingredient_text, parse_ingredient_list

samples = [
    "2 cups rice",
    "1 tbsp ghee",
    "a pinch of salt",
    "a handful of coriander leaves",
    "1 1/2 tsp sugar",
    "salt to taste",
    "2 cubes paneer",
    "kasuri methi (crushed)",
]

for item in samples:
    print(parse_ingredient_text(item))

print(parse_ingredient_list(samples))
print("Ingredient parser test passed")