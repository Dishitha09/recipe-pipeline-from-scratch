from __future__ import annotations

import time
from typing import Any, Dict, List

from scraping.plugins.base_plugin import RecipeSourcePlugin
from scraping.web_scraper import scrape_recipe
from utils.logging_config import get_logger


logger = get_logger("hebbars_plugin")


class HebbarsKitchenPlugin(RecipeSourcePlugin):
    def scrape(self, urls: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        for idx, url in enumerate(urls, start=1):
            try:
                item = scrape_recipe(url)
                results.append(item)
                logger.info("OK %s -> %s", idx, item.get("title"))
            except Exception as exc:
                logger.error("FAIL %s -> %s :: %s", idx, url, exc)

            time.sleep(1)

        return results