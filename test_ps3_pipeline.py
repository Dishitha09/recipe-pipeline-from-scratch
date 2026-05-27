import csv

from preprocessing.coerce import coerce_raw_record
from enrichment.enrich_recipe import enrich_recipe


with open("data/raw/demo_recipes.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

preprocessed = [coerce_raw_record(row) for row in rows]
enriched = [enrich_recipe(recipe) for recipe in preprocessed]

for item in enriched:
    print(item)
    print("-" * 50)

assert enriched[-1]["ingredients_enriched"][0]["canonical_name"] == "whole wheat flour"
assert enriched[-1]["ingredients_enriched"][0]["resolution_type"] == "exact"

print("PS-3 pipeline test passed")