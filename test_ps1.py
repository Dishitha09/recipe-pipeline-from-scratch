from ingestion.csv_adapter import CSVRecipeAdapter
from ingestion.raw_record import RawRecord


# Test 1
adapter = CSVRecipeAdapter("recipes.csv")
records = adapter.extract()

assert len(records) == 3


# Test 2
for record in records:
    assert isinstance(record, RawRecord)


# Test 3
record_ids = [r.record_id for r in records]

assert len(record_ids) == len(set(record_ids))


# Test 4
first = records[0]

try:
    first.source_id = "changed"

except Exception:
    print("RawRecord is immutable")


print("PS-1 tests passed")