from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "tracking" / "url_registry.json"


def load_registry():
    if not REGISTRY_PATH.exists():
        return []

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load_registry()

    total = len(data)
    discovered = sum(1 for x in data if x.get("status") == "discovered")
    scraped = sum(1 for x in data if x.get("status") == "scraped")
    failed = sum(1 for x in data if x.get("status") == "failed")
    recipe_found = sum(1 for x in data if x.get("recipe_found") is True)

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