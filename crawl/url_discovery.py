from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from typing import Iterable, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .crawl_queue import normalize_url


RECIPE_HINTS = (
    "recipe",
    "recipes",
    "cook",
    "cooking",
    "how-to-make",
    "how-to",
    "food",
    "dish",
    "recipe-card",
)


def load_urls_from_file(path: str | Path) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if file_path.suffix.lower() in {".json", ".jsonl"}:
        try:
            payload = json.loads(text)
            if isinstance(payload, list):
                return [str(item).strip() for item in payload if str(item).strip()]
            if isinstance(payload, dict):
                for key in ("urls", "items", "data"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        return [str(item).strip() for item in value if str(item).strip()]
        except Exception:
            pass

    return [line.strip() for line in text.splitlines() if line.strip()]


def _same_domain(url: str, domain_allowlist: Optional[Set[str]]) -> bool:
    if not domain_allowlist:
        return True
    host = urlparse(url).netloc.lower()
    return any(host.endswith(domain) for domain in domain_allowlist)


def _looks_like_recipe_url(url: str) -> bool:
    lower = url.lower()
    return any(hint in lower for hint in RECIPE_HINTS)


def discover_from_sitemap(
    sitemap_url: str,
    allowed_domains: Optional[Set[str]] = None,
    timeout: int = 20,
    max_urls: int = 10000,
) -> List[str]:
    discovered: List[str] = []
    seen_sitemaps: Set[str] = set()
    seen_urls: Set[str] = set()

    def walk(url: str) -> None:
        if len(discovered) >= max_urls:
            return

        normalized_sitemap = normalize_url(url)
        if normalized_sitemap in seen_sitemaps:
            return
        seen_sitemaps.add(normalized_sitemap)

        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        tag = root.tag.lower()

        if tag.endswith("sitemapindex"):
            for loc in root.findall(".//{*}loc"):
                if loc.text and loc.text.strip():
                    walk(loc.text.strip())
            return

        for loc in root.findall(".//{*}loc"):
            if len(discovered) >= max_urls:
                break
            if not loc.text:
                continue
            candidate = normalize_url(loc.text.strip())
            if not candidate or candidate in seen_urls:
                continue
            if allowed_domains and not _same_domain(candidate, allowed_domains):
                continue
            seen_urls.add(candidate)
            discovered.append(candidate)

    walk(sitemap_url)
    return discovered


def discover_from_html(
    start_url: str,
    allowed_domains: Optional[Set[str]] = None,
    timeout: int = 20,
    max_depth: int = 1,
    max_urls: int = 10000,
) -> List[str]:
    start = normalize_url(start_url)
    if not start:
        return []

    discovered: List[str] = []
    seen: Set[str] = set()
    queue = deque([(start, 0)])

    while queue and len(discovered) < max_urls:
        current_url, depth = queue.popleft()
        if current_url in seen:
            continue
        seen.add(current_url)

        try:
            resp = requests.get(current_url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            absolute = normalize_url(urljoin(current_url, href))
            if not absolute or absolute in seen:
                continue
            if not _same_domain(absolute, allowed_domains):
                continue

            if _looks_like_recipe_url(absolute):
                discovered.append(absolute)

            if depth < max_depth and absolute not in seen:
                queue.append((absolute, depth + 1))

    return discovered


def discover_urls(
    url_files: Optional[List[str]] = None,
    sitemap_urls: Optional[List[str]] = None,
    html_seed_urls: Optional[List[str]] = None,
    allowed_domains: Optional[Iterable[str]] = None,
    max_urls: int = 10000,
) -> List[str]:
    domain_set = {d.lower().lstrip(".") for d in allowed_domains or [] if d.strip()}
    discovered: List[str] = []
    seen: Set[str] = set()

    def add_many(urls: Iterable[str]) -> None:
        for url in urls:
            normalized = normalize_url(url)
            if not normalized or normalized in seen:
                continue
            if domain_set and not _same_domain(normalized, domain_set):
                continue
            seen.add(normalized)
            discovered.append(normalized)
            if len(discovered) >= max_urls:
                return

    for file_path in url_files or []:
        add_many(load_urls_from_file(file_path))
        if len(discovered) >= max_urls:
            return discovered

    for sitemap in sitemap_urls or []:
        add_many(discover_from_sitemap(sitemap, allowed_domains=domain_set or None, max_urls=max_urls))
        if len(discovered) >= max_urls:
            return discovered

    for html_seed in html_seed_urls or []:
        add_many(discover_from_html(html_seed, allowed_domains=domain_set or None, max_depth=1, max_urls=max_urls))
        if len(discovered) >= max_urls:
            return discovered

    return discovered


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover recipe URLs from files, sitemaps, or HTML pages.")
    parser.add_argument("--url-file", action="append", default=[], help="Text/JSON file containing URLs")
    parser.add_argument("--sitemap", action="append", default=[], help="Sitemap XML or sitemap index URL")
    parser.add_argument("--seed", action="append", default=[], help="HTML seed pages to explore")
    parser.add_argument("--allow-domain", action="append", default=[], help="Allowed domain suffix, e.g. hebbarskitchen.com")
    parser.add_argument("--max-urls", type=int, default=10000)
    parser.add_argument("--output", default="data/discovered_urls.txt")
    args = parser.parse_args()

    urls = discover_urls(
        url_files=args.url_file,
        sitemap_urls=args.sitemap,
        html_seed_urls=args.seed,
        allowed_domains=args.allow_domain,
        max_urls=args.max_urls,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(urls), encoding="utf-8")

    print(f"Discovered {len(urls)} URLs")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()