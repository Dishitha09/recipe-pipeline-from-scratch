import json
from pathlib import Path

INPUT = Path("data/final_recipes.json")
OUTPUT = Path("processed_data/normalized_recipes_clean.json")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(INPUT, "r", encoding="utf-8") as f:
    records = json.load(f)

normalized = []

for record in records:
    raw = record.get("raw_content", {})

    normalized.append(
        {
            "title": raw.get("title"),
            "source_url": raw.get("source_url"),
            "ingredients": raw.get("ingredients", []),
            "steps": raw.get("steps", []),
            "cuisine": "Indian",
            "source_name": record.get("source_id", "crawl_source"),
            "prep_time_minutes": None,
            "servings": None,
            "raw_json_ld": record,
        }
    )

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(normalized, f, indent=2, ensure_ascii=False)

print(f"Converted {len(normalized)} recipes")
print(f"Saved to {OUTPUT}")