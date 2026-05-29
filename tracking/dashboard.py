import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/registry.db")


def safe_count(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return len(json.load(f))
    except Exception:
        return 0


def main():
    print("\n" + "=" * 40)
    print("PIPELINE DASHBOARD")
    print("=" * 40)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        total_urls = cur.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
    except Exception:
        total_urls = 0

    try:
        discovered_urls = cur.execute(
            "SELECT COUNT(*) FROM urls WHERE status='discovered'"
        ).fetchone()[0]
    except Exception:
        discovered_urls = 0

    try:
        scraped_urls = cur.execute(
            "SELECT COUNT(*) FROM urls WHERE status='scraped'"
        ).fetchone()[0]
    except Exception:
        scraped_urls = 0

    try:
        failed_urls = cur.execute(
            "SELECT COUNT(*) FROM urls WHERE status='failed'"
        ).fetchone()[0]
    except Exception:
        failed_urls = 0

    try:
        latest_run = cur.execute(
            """
            SELECT source_name, status, scraped_count, started_at, finished_at
            FROM crawl_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    except Exception:
        latest_run = None

    conn.close()

    raw = safe_count("data/raw/hebbars_kitchen_recipes.json")
    accepted = safe_count("processed_data/accepted_recipes.json")
    rejected = safe_count("quarantine/rejected_recipes.json")
    normalized = safe_count("processed_data/normalized_recipes.json")

    print(f"\nURLs Tracked      : {total_urls}")
    print(f"URLs Discovered   : {discovered_urls}")
    print(f"URLs Scraped      : {scraped_urls}")
    print(f"URLs Failed       : {failed_urls}")

    print(f"\nRecipes Raw       : {raw}")
    print(f"Recipes Normalized: {normalized}")
    print(f"Recipes Accepted  : {accepted}")
    print(f"Recipes Rejected  : {rejected}")

    if latest_run:
        print("\nLatest Crawl")
        print("-" * 20)
        print(f"Source   : {latest_run[0]}")
        print(f"Status   : {latest_run[1]}")
        print(f"Scraped  : {latest_run[2]}")
        print(f"Started  : {latest_run[3]}")
        print(f"Finished : {latest_run[4]}")

    print("\n" + "=" * 40)


if __name__ == "__main__":
    main()