import csv
from preprocessing.coerce import coerce_raw_record


with open("data/raw/demo_recipes.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(rows)

records = [coerce_raw_record(row) for row in rows]

for record in records:
    print(record)

assert records[0].title == "Paneer Butter Masala"
assert records[0].prep_time == 45
assert records[0].ingredients == ["paneer", "butter", "tomato"]
assert records[0].steps == ["cook", "serve"]

print("PS-2 test passed")