from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "registry.db"


def load_rows():
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT url, source_name, status, discovered_at, scraped_at, recipe_found, attempts, last_error FROM urls").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def main():
    data = load_rows()

    total = len(data)
    discovered = sum(1 for x in data if x.get("status") == "discovered")
    scraped = sum(1 for x in data if x.get("status") == "scraped")
    failed = sum(1 for x in data if x.get("status") == "failed")
    recipe_found = sum(1 for x in data if x.get("recipe_found") == 1)

    domains = Counter()
    for item in data:
        url = item.get("url", "")
        if url:
            domains[urlparse(url).netloc] += 1

    print("\n========== URL REGISTRY STATS ==========\n")
    print(f"Total URLs   : {total}")
    print(f"Discovered   : {discovered}")
    print(f"Scraped      : {scraped}")
    print(f"Failed       : {failed}")
    print(f"Recipe Found : {recipe_found}")

    print("\nTop Domains:\n")
    for domain, count in domains.most_common(10):
        print(f"{domain:<40} {count}")

    print("\n========================================\n")


if __name__ == "__main__":
    main()