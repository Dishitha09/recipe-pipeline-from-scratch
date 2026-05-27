from ingestion.json_adapter import JSONRecipeAdapter
from preprocessing.coerce import coerce_raw_record
from enrichment.enrich_recipe import enrich_recipe
from normalization.normalize_recipe import normalize_recipe
from validation.validator import validate_recipe


adapter = JSONRecipeAdapter("data/raw/web_recipes.json")
raw_records = adapter.extract()

print(f"Loaded {len(raw_records)} RawRecords")
print(raw_records[0])

first_raw = raw_records[0].raw_content
preprocessed = coerce_raw_record(first_raw)
print(preprocessed)

enriched = enrich_recipe(preprocessed)
print(enriched)

normalized = normalize_recipe(enriched)
print(normalized)

validated = validate_recipe(normalized)
print(validated["verdict"])
print("Web ingestion pipeline passed")