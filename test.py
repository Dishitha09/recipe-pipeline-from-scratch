from ingestion.registry import SOURCE_REGISTRY


adapter_class = SOURCE_REGISTRY["kaggle_csv"]

adapter = adapter_class("recipes.csv")

records = adapter.extract()

for record in records:
    print(record)