from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .raw_record import RawRecord
from .source_adapter import SourceAdapter


class WebScraperAdapter(SourceAdapter):
    def __init__(
        self,
        source_id: str,
        source_type: str = "web",
        version: str = "1.0",
        urls: Optional[List[str]] = None,
        url_file: Optional[str] = None,
        timeout: int = 15,
        user_agent: str = "Mozilla/5.0",
    ) -> None:
        super().__init__(source_id=source_id, source_type=source_type, version=version)
        self.urls = urls or []
        self.url_file = url_file
        self.timeout = timeout
        self.user_agent = user_agent
        self.errors: List[Dict[str, Any]] = []

    def validate_config(self) -> None:
        if not self.urls and not self.url_file:
            raise ValueError("WebScraperAdapter requires either urls or url_file")

        if self.url_file:
            path = Path(self.url_file)
            if not path.exists():
                raise FileNotFoundError(f"URL file not found: {path}")

    def _load_urls(self) -> List[str]:
        if self.urls:
            return [u.strip() for u in self.urls if str(u).strip()]

        if self.url_file:
            path = Path(self.url_file)
            lines = path.read_text(encoding="utf-8").splitlines()
            return [line.strip() for line in lines if line.strip()]

        return []

    def extract(self) -> List[RawRecord]:
        self.validate_config()
        self.errors = []

        records: List[RawRecord] = []
        for url in self._load_urls():
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                recipe_data, json_ld_found = self._extract_recipe_data(soup, url)

                record = RawRecord(
                    source_id=self.source_id,
                    source_type=self.source_type,
                    version=self.version,
                    raw_content=recipe_data,
                    metadata={
                        "url": url,
                        "status_code": response.status_code,
                        "json_ld_found": json_ld_found,
                        "adapter": "WebScraperAdapter",
                    },
                )
                records.append(record)

            except Exception as exc:
                self.errors.append(
                    {
                        "url": url,
                        "source_id": self.source_id,
                        "error": str(exc),
                    }
                )

        return records

    def _extract_recipe_data(self, soup: BeautifulSoup, url: str) -> tuple[Dict[str, Any], bool]:
        json_ld = self._extract_json_ld_recipe(soup)
        if json_ld:
            return self._build_from_json_ld(json_ld, soup, url), True

        return self._build_from_css(soup, url), False

    def _extract_json_ld_recipe(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
            raw = script.string or script.get_text(strip=True)
            if not raw:
                continue

            try:
                payload = json.loads(raw)
            except Exception:
                continue

            recipe = self._find_recipe_object(payload)
            if recipe:
                return recipe

        return None

    def _find_recipe_object(self, payload: Any) -> Optional[Dict[str, Any]]:
        if isinstance(payload, dict):
            type_value = payload.get("@type")

            if type_value == "Recipe":
                return payload

            if isinstance(type_value, list) and any(str(t).lower() == "recipe" for t in type_value):
                return payload

            if "@graph" in payload:
                found = self._find_recipe_object(payload["@graph"])
                if found:
                    return found

            for value in payload.values():
                found = self._find_recipe_object(value)
                if found:
                    return found

        if isinstance(payload, list):
            for item in payload:
                found = self._find_recipe_object(item)
                if found:
                    return found

        return None

    def _build_from_json_ld(self, data: Dict[str, Any], soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = self._first_non_empty(
            data.get("name"),
            self._meta_title(soup),
            self._h1_title(soup),
        )

        ingredients = self._as_list(data.get("recipeIngredient"))
        steps = self._extract_instructions(data.get("recipeInstructions"))

        return {
            "title": title,
            "source_url": url,
            "ingredients": ingredients,
            "steps": steps,
            "cuisine": self._normalize_single_value(data.get("recipeCuisine")),
            "prep_time": self._duration_to_minutes(data.get("prepTime") or data.get("totalTime")),
            "cook_time": self._duration_to_minutes(data.get("cookTime")),
            "servings": self._normalize_single_value(data.get("recipeYield")),
            "json_ld_found": True,
            "raw_json_ld": data,
        }

    def _build_from_css(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = self._first_non_empty(self._h1_title(soup), self._meta_title(soup), "Untitled Recipe")

        ingredients = self._select_texts(
            soup,
            [
                "li[class*='ingredient']",
                ".ingredients li",
                ".ingredient",
                "[class*='ingredient'] li",
            ],
        )
        steps = self._select_texts(
            soup,
            [
                "li[class*='instruction']",
                "li[class*='direction']",
                ".instructions li",
                ".instruction",
                ".direction",
                "ol li",
            ],
        )

        return {
            "title": title,
            "source_url": url,
            "ingredients": ingredients,
            "steps": steps,
            "cuisine": None,
            "prep_time": None,
            "cook_time": None,
            "servings": None,
            "json_ld_found": False,
            "raw_json_ld": None,
        }

    def _select_texts(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        items: List[str] = []
        for selector in selectors:
            for tag in soup.select(selector):
                text = tag.get_text(" ", strip=True)
                if text and text not in items:
                    items.append(text)
        return items

    def _extract_instructions(self, instructions: Any) -> List[str]:
        if isinstance(instructions, str):
            parts = re.split(r"[\n.;•]+", instructions)
            return [part.strip() for part in parts if part.strip()]

        if isinstance(instructions, dict):
            if "text" in instructions:
                text = str(instructions["text"]).strip()
                return [text] if text else []
            if "itemListElement" in instructions:
                return self._extract_instructions(instructions["itemListElement"])

        if isinstance(instructions, list):
            steps: List[str] = []
            for item in instructions:
                if isinstance(item, dict):
                    if "text" in item:
                        text = str(item["text"]).strip()
                        if text:
                            steps.append(text)
                    elif "itemListElement" in item:
                        steps.extend(self._extract_instructions(item["itemListElement"]))
                else:
                    text = str(item).strip()
                    if text:
                        steps.append(text)
            return steps

        return []

    def _as_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if value is None:
            return []
        text = str(value).strip()
        return [text] if text else []

    def _normalize_single_value(self, value: Any) -> Optional[str]:
        if isinstance(value, list):
            value = next((str(v).strip() for v in value if str(v).strip()), None)
        if value is None:
            return None

        text = str(value).strip()
        return text or None

    def _duration_to_minutes(self, value: Any) -> Optional[int]:
        if value is None:
            return None

        text = str(value).strip().upper()

        iso_match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", text)
        if iso_match:
            hours = int(iso_match.group(1) or 0)
            minutes = int(iso_match.group(2) or 0)
            return hours * 60 + minutes

        plain_match = re.search(r"(\d+)\s*MIN", text)
        if plain_match:
            return int(plain_match.group(1))

        return None

    def _meta_title(self, soup: BeautifulSoup) -> Optional[str]:
        meta = soup.find("meta", attrs={"property": "og:title"})
        if meta and meta.get("content"):
            return meta["content"].strip()

        meta = soup.find("meta", attrs={"name": "title"})
        if meta and meta.get("content"):
            return meta["content"].strip()

        if soup.title and soup.title.get_text(strip=True):
            return soup.title.get_text(strip=True)

        return None

    def _h1_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(" ", strip=True)
            return text or None
        return None

    def _first_non_empty(self, *values: Any) -> Optional[str]:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None