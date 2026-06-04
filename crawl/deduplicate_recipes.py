from __future__ import annotations

import json
from pathlib import Path

INPUT_FILE = Path("data/final_recipes_raw.json")
OUTPUT_FILE = Path("data/final_recipes.json")


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    unique_urls = {}
    duplicates = 0

    for record in records:

        raw = record.get("raw_content", {})

        url = raw.get("source_url")

        if not url:
            continue

        if url in unique_urls:
            duplicates += 1
            continue

        unique_urls[url] = record

    final_records = list(unique_urls.values())

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            final_records,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("=" * 50)
    print(f"Input records : {len(records)}")
    print(f"Duplicates    : {duplicates}")
    print(f"Final records : {len(final_records)}")
    print(f"Saved to      : {OUTPUT_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()