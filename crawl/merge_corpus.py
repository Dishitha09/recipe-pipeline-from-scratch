from __future__ import annotations

import json
from pathlib import Path


RUNS_DIR = Path("runs/crawl_batches")
OUTPUT_FILE = Path("data/final_recipes_raw.json")


def load_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def main():
    all_records = []

    run_dirs = sorted(
        [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    )

    print(f"Found {len(run_dirs)} run folders")

    for run_dir in run_dirs:
        records_file = run_dir / "records_clean.json"

        if not records_file.exists():
            continue

        records = load_json(records_file)

        print(
            f"{run_dir.name:<30} "
            f"{len(records):>6} records"
        )

        all_records.extend(records)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            all_records,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 50)
    print(f"Merged records : {len(all_records)}")
    print(f"Saved to       : {OUTPUT_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()