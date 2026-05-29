from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import scrapy

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tracking.url_registry_db import (  # noqa: E402
    initialize_database,
    record_url,
    mark_scraped,
    record_crawl_run,
)


initialize_database()

CHECKPOINT_FILE = PROJECT_ROOT / "crawl_checkpoint.json"


class HebbarsSpider(scrapy.Spider):
    name = "hebbars"
    allowed_domains = ["hebbarskitchen.com"]
    start_urls = ["https://hebbarskitchen.com/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "DEPTH_LIMIT": 3,
        "LOG_LEVEL": "INFO",
    }

    recipe_keywords = (
        "recipe",
        "masala",
        "curry",
        "dosa",
        "paneer",
        "chole",
        "bhature",
        "sambar",
        "aloo",
        "pulao",
        "dal",
        "rice",
        "snack",
        "sabzi",
        "bhaji",
    )

    skip_keywords = (
        "/tag/",
        "/category/",
        "/author/",
        "/page/",
        "/wp-content/",
        "/feed",
        "/privacy",
        "/contact",
        "/about",
        "/terms",
        "/comment",
        "/video",
        "/search",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_count = 0
        self.seen_urls = set()
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.last_recipe_url = None
        self.last_recipe_title = None

    def parse(self, response: scrapy.http.Response):
        current_url = self.canonicalize_url(response.url)
        record_url(current_url, source_name="Hebbars Kitchen")

        recipe = self.extract_recipe(response)
        if recipe:
            self.scraped_count += 1
            self.last_recipe_url = current_url
            self.last_recipe_title = recipe.get("title")
            mark_scraped(current_url, recipe_found=True)
            yield recipe
        else:
            mark_scraped(current_url, recipe_found=False)

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue

            next_url = self.canonicalize_url(response.urljoin(href))

            if next_url in self.seen_urls:
                continue

            if self.should_follow(next_url):
                self.seen_urls.add(next_url)
                record_url(next_url, source_name="Hebbars Kitchen")
                yield response.follow(next_url, callback=self.parse)

    def canonicalize_url(self, url: str) -> str:
        parts = urlparse(url)
        return parts._replace(fragment="").geturl()

    def should_follow(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.netloc not in {"hebbarskitchen.com", "www.hebbarskitchen.com"}:
            return False

        path = parsed.path.lower()

        if any(skip in path for skip in self.skip_keywords):
            return False

        if path in {"", "/"}:
            return True

        return any(keyword in path for keyword in self.recipe_keywords)

    def extract_recipe(self, response: scrapy.http.Response) -> Optional[Dict[str, Any]]:
        json_ld_recipe = self.extract_json_ld_recipe(response)
        if not json_ld_recipe:
            return None

        title = json_ld_recipe.get("name") or self.extract_title(response)
        ingredients = json_ld_recipe.get("recipeIngredient", []) or []
        steps = self.normalize_instructions(json_ld_recipe.get("recipeInstructions", []))
        cuisine = json_ld_recipe.get("recipeCuisine")
        prep_time = json_ld_recipe.get("prepTime") or json_ld_recipe.get("totalTime")
        servings = json_ld_recipe.get("recipeYield")
        recipe_category = self.normalize_to_list(json_ld_recipe.get("recipeCategory"))

        if isinstance(servings, list):
            servings = servings[0] if servings else None

        if not self.is_valid_recipe(title, ingredients, steps, recipe_category):
            return None

        return {
            "source_id": "hebbars_spider",
            "source_type": "web",
            "source_name": "Hebbars Kitchen",
            "source_url": self.canonicalize_url(response.url),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "cuisine": cuisine,
            "prep_time": prep_time,
            "servings": servings,
            "recipe_category": recipe_category,
            "ingredients": ingredients,
            "steps": steps,
            "raw_json_ld": json_ld_recipe,
        }

    def is_valid_recipe(
        self,
        title: str,
        ingredients: List[Any],
        steps: List[str],
        recipe_category: List[str],
    ) -> bool:
        if not title or len(title.strip()) < 3:
            return False

        if len(ingredients) < 2:
            return False

        if len(steps) < 1:
            return False

        if any("tip" in cat.lower() for cat in recipe_category):
            return False

        return True

    def normalize_to_list(self, value: Any) -> List[str]:
        if not value:
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        text = str(value).strip()
        return [text] if text else []

    def extract_title(self, response: scrapy.http.Response) -> str:
        h1 = response.css("h1::text").get()
        if h1 and h1.strip():
            return h1.strip()

        title = response.css("title::text").get()
        if title and title.strip():
            return title.strip()

        return "Untitled Recipe"

    def extract_json_ld_recipe(self, response: scrapy.http.Response) -> Optional[Dict[str, Any]]:
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()

        for raw_text in scripts:
            raw_text = raw_text.strip()
            if not raw_text:
                continue

            try:
                data = json.loads(raw_text)
            except Exception:
                continue

            recipe = self.find_recipe_object(data)
            if recipe:
                return recipe

        return None

    def find_recipe_object(self, payload: Any) -> Optional[Dict[str, Any]]:
        if isinstance(payload, dict):
            type_value = payload.get("@type")

            if type_value == "Recipe" or (
                isinstance(type_value, list) and "Recipe" in type_value
            ):
                return payload

            if "@graph" in payload:
                found = self.find_recipe_object(payload["@graph"])
                if found:
                    return found

            for value in payload.values():
                found = self.find_recipe_object(value)
                if found:
                    return found

        if isinstance(payload, list):
            for item in payload:
                found = self.find_recipe_object(item)
                if found:
                    return found

        return None

    def normalize_instructions(self, instructions: Any) -> List[str]:
        steps: List[str] = []

        if isinstance(instructions, str):
            parts = re.split(r"[\n.;•]+", instructions)
            return [part.strip() for part in parts if part.strip()]

        if isinstance(instructions, dict):
            if "text" in instructions:
                text = str(instructions["text"]).strip()
                if text:
                    return [text]

            if "itemListElement" in instructions:
                return self.normalize_instructions(instructions["itemListElement"])

        if isinstance(instructions, list):
            for item in instructions:
                if isinstance(item, dict):
                    if "text" in item:
                        text = str(item["text"]).strip()
                        if text:
                            steps.append(text)
                    elif "itemListElement" in item:
                        steps.extend(self.normalize_instructions(item["itemListElement"]))
                else:
                    text = str(item).strip()
                    if text:
                        steps.append(text)

        return steps

    def closed(self, reason):
        finished_at = datetime.now(timezone.utc).isoformat()

        checkpoint = {
            "status": "completed",
            "reason": reason,
            "started_at": self.started_at,
            "finished_at": finished_at,
            "scraped_count": self.scraped_count,
            "last_recipe_url": self.last_recipe_url,
            "last_recipe_title": self.last_recipe_title,
            "visited_urls_count": len(self.seen_urls),
        }

        CHECKPOINT_FILE.write_text(
            json.dumps(checkpoint, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        try:
            record_crawl_run(
                source_name="Hebbars Kitchen",
                started_at=self.started_at,
                finished_at=finished_at,
                status=reason,
                scraped_count=self.scraped_count,
                notes=f"Last recipe: {self.last_recipe_title or ''}",
            )
        except Exception as exc:
            self.logger.error("Failed to record crawl run: %s", exc)