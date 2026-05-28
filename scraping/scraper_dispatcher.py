from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from scraping.web_scraper import scrape_recipe
from tracking.scrape_tracker import add_source, update_source_status
from utils.logging_config import get_logger


CONFIG_PATH = Path("configs/sources.json")
RAW_DIR = Path("data/raw")

logger = get_logger("scraper_dispatcher")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80] or "source"


def load_sources() -> List[Dict[str, Any]]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("configs/sources.json must contain a JSON list")

    return data


def load_urls(url_file: str) -> List[str]:
    path = Path(url_file)

    if not path.exists():
        raise FileNotFoundError(f"Missing URL file: {path}")

    urls: List[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith("HEBBARS_URLS"):
            continue

        line = line.strip('",\' ')
        line = line.rstrip(",")

        if line.startswith("http://") or line.startswith("https://"):
            urls.append(line)

    return urls


def save_source_output(source_name: str, records: List[Dict[str, Any]]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DIR / f"{slugify(source_name)}_recipes.json"

    output_path.write_text(
        json.dumps(
            {
                "source_name": source_name,
                "recipes": records,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path


def run_source(source_config: Dict[str, Any]) -> Dict[str, Any]:
    source_name = source_config["source_name"]
    source_type = source_config["source_type"]
    base_url = source_config["base_url"]
    url_file = source_config["url_file"]
    enabled = source_config.get("enabled", True)
    scraper = source_config.get("scraper", "web")

    if not enabled:
        logger.info("Skipping disabled source: %s", source_name)
        return {
            "source_name": source_name,
            "status": "skipped",
            "recipes_scraped": 0,
        }

    add_source(
        source_name=source_name,
        source_type=source_type,
        base_url=base_url,
    )

    update_source_status(
        base_url=base_url,
        status="in_progress",
        recipes_scraped=0,
        notes="Dispatcher started scraping",
    )

    urls = load_urls(url_file)
    logger.info("Source=%s URLs=%d", source_name, len(urls))

    scraped: List[Dict[str, Any]] = []

    for idx, url in enumerate(urls, start=1):
        try:
            if scraper != "web":
                raise NotImplementedError(
                    f"Scraper '{scraper}' not implemented yet"
                )

            item = scrape_recipe(url)
            item["source_name"] = source_name
            scraped.append(item)

            logger.info("OK %s -> %s", idx, item.get("title"))

            update_source_status(
                base_url=base_url,
                status="in_progress",
                recipes_scraped=len(scraped),
                notes=f"Scraped {len(scraped)} recipes so far",
            )

        except Exception as exc:
            logger.error("FAIL %s -> %s :: %s", idx, url, exc)

        time.sleep(1)

    output_path = save_source_output(source_name, scraped)

    final_status = "completed" if scraped else "failed"

    update_source_status(
        base_url=base_url,
        status=final_status,
        recipes_scraped=len(scraped),
        notes=f"Dispatcher finished with status={final_status}",
    )

    logger.info(
        "Saved %d recipes for %s to %s",
        len(scraped),
        source_name,
        output_path,
    )

    return {
        "source_name": source_name,
        "status": final_status,
        "recipes_scraped": len(scraped),
        "output_path": str(output_path),
    }


def main() -> None:
    sources = load_sources()
    logger.info("Loaded %d source configs", len(sources))

    results: List[Dict[str, Any]] = []

    for source_config in sources:
        try:
            result = run_source(source_config)
            results.append(result)
        except Exception as exc:
            logger.exception(
                "Source failed completely: %s",
                source_config.get("source_name"),
            )
            results.append(
                {
                    "source_name": source_config.get("source_name", "unknown"),
                    "status": "failed",
                    "error": str(exc),
                }
            )

    summary = {
        "total_sources": len(results),
        "completed": sum(1 for r in results if r.get("status") == "completed"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        "total_recipes": sum(r.get("recipes_scraped", 0) for r in results),
    }

    logger.info("Dispatcher summary: %s", summary)
    print(summary)


if __name__ == "__main__":
    main()