from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

URLS_PATH = Path("data/raw/recipe_urls.txt")
RAW_OUTPUT_PATH = Path("data/raw/web_recipes.json")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80] or "recipe"


def load_urls(path: Path = URLS_PATH) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing URL file: {path}")

    urls: List[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("HEBBARS_URLS"):
            continue

        line = line.strip('",\' ')
        line = line.rstrip(",")

        if line.startswith("http://") or line.startswith("https://"):
            urls.append(line)

    return urls


def safe_get(url: str) -> requests.Response:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response


def extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        if text:
            return text

    if soup.title:
        title_text = soup.title.get_text(" ", strip=True)
        if title_text:
            return title_text

    return "Untitled Recipe"


def extract_text_after_heading(
    soup: BeautifulSoup,
    heading_keywords: List[str],
) -> List[str]:
    """
    Find a heading that contains one of the keywords, then collect list items
    and short paragraphs that follow until the next heading.
    """
    headings = soup.find_all(["h1", "h2", "h3", "h4"])

    for heading in headings:
        heading_text = heading.get_text(" ", strip=True).lower()

        if not any(keyword.lower() in heading_text for keyword in heading_keywords):
            continue

        collected: List[str] = []

        for sibling in heading.find_all_next():
            if sibling == heading:
                continue

            if sibling.name in ["h1", "h2", "h3", "h4"]:
                break

            if sibling.name in ["ul", "ol"]:
                for li in sibling.find_all("li"):
                    text = li.get_text(" ", strip=True)
                    if text:
                        collected.append(text)

            elif sibling.name == "p":
                text = sibling.get_text(" ", strip=True)
                if text:
                    collected.append(text)

        if collected:
            return collected

    return []


def extract_json_ld_recipe(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Try to read Recipe structured data from JSON-LD if the page has it.
    """
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw_text = script.string or script.get_text(strip=True)
        if not raw_text:
            continue

        try:
            data = json.loads(raw_text)
        except Exception:
            continue

        recipe = find_recipe_object(data)
        if recipe:
            return recipe

    return None


def find_recipe_object(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        type_value = payload.get("@type")

        if type_value == "Recipe" or (
            isinstance(type_value, list) and "Recipe" in type_value
        ):
            return payload

        if "@graph" in payload:
            found = find_recipe_object(payload["@graph"])
            if found:
                return found

        for value in payload.values():
            found = find_recipe_object(value)
            if found:
                return found

    if isinstance(payload, list):
        for item in payload:
            found = find_recipe_object(item)
            if found:
                return found

    return None


def normalize_instructions(instructions: Any) -> List[str]:
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
            return normalize_instructions(instructions["itemListElement"])

    if isinstance(instructions, list):
        for item in instructions:
            if isinstance(item, dict):
                if "text" in item:
                    text = str(item["text"]).strip()
                    if text:
                        steps.append(text)
                elif "itemListElement" in item:
                    steps.extend(normalize_instructions(item["itemListElement"]))
            else:
                text = str(item).strip()
                if text:
                    steps.append(text)

    return steps


def scrape_recipe(url: str) -> Dict[str, Any]:
    response = safe_get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    json_ld = extract_json_ld_recipe(soup)
    title = extract_title(soup)

    if json_ld:
        title = json_ld.get("name") or title
        ingredients = json_ld.get("recipeIngredient", []) or []
        steps = normalize_instructions(json_ld.get("recipeInstructions", []))
        cuisine = json_ld.get("recipeCuisine")
        prep_time = json_ld.get("prepTime") or json_ld.get("totalTime")
        servings = json_ld.get("recipeYield")
    else:
        ingredients = extract_text_after_heading(soup, ["ingredients"])
        steps = extract_text_after_heading(
            soup,
            ["instructions", "method", "preparation", "how to make", "recipe"],
        )
        cuisine = None
        prep_time = None
        servings = None

    return {
        "source_id": slugify(urlparse(url).netloc),
        "source_type": "web",
        "source_url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "cuisine": cuisine,
        "prep_time": prep_time,
        "servings": servings,
        "ingredients": ingredients,
        "steps": steps,
        "raw_json_ld": json_ld,
    }


def main() -> None:
    urls = load_urls()
    print(f"Found {len(urls)} URLs")

    scraped: List[Dict[str, Any]] = []

    for url in urls[:10]:
        try:
            item = scrape_recipe(url)
            scraped.append(item)
            print(f"OK   -> {item['title']}")
        except Exception as exc:
            print(f"FAIL -> {url} :: {exc}")

        time.sleep(1)

    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUTPUT_PATH.write_text(
        json.dumps({"recipes": scraped}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved {len(scraped)} recipes to {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    main()