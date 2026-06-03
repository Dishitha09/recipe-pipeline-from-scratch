from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse, urlunparse


ASSET_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".bmp", ".tif", ".tiff",
    ".pdf", ".mp3", ".wav", ".mp4", ".mov",
}

BLOCKED_KEYWORDS = {
    "benefit", "benefits", "health", "remedy", "remedies", "beauty",
    "contact", "about", "privacy", "disclaimer", "terms", "policy",
    "author", "tag", "category", "sitemap", "feed", "comment", "comments",
    "login", "signup", "gallery", "photo", "photos",
    "top-7", "top-8", "top-9", "top-10",
    "clean", "maintain", "wrong-kitchen", "kitchen-tips",
    "toddler-protein", "vessels", "silver", "copper",
}

BLOCKED_SEGMENTS = {
    "category", "tag", "author", "page", "feed", "comments", "comment",
    "sitemap", "search", "privacy", "contact", "about", "disclaimer", "terms",
}

def normalize_url(url: str) -> str:
    value = str(url).strip()
    if not value:
        return ""

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return ""

    scheme = "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"

    return urlunparse((scheme, netloc, path, "", "", ""))


def is_probably_recipe_url(url: str) -> bool:
    value = normalize_url(url)
    if not value:
        return False

    parsed = urlparse(value)
    full = value.lower()
    path = parsed.path.lower().strip("/")

    if not path:
        return False

    if any(path.endswith(ext) for ext in ASSET_EXTENSIONS):
        return False

    if "/wp-content/" in full or "/uploads/" in full:
        return False

    segments = [seg for seg in path.split("/") if seg]
    if any(seg in BLOCKED_SEGMENTS for seg in segments):
        return False

    if any(keyword in full for keyword in BLOCKED_KEYWORDS):
        return False

    if path in {"recipe", "recipes", "post", "posts"}:
        return False

    # Very short / generic pages are usually not recipes
    slug = segments[-1]
    if len(slug) < 5:
        return False

    return True


def read_urls_from_file(path: Path) -> Iterable[str]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        value = line.strip()
        if value:
            yield value


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter discovered URLs down to likely recipe pages.")
    parser.add_argument("--input-dir", default="data/discovered", help="Directory containing discovered URL .txt files")
    parser.add_argument("--output", default="data/recipe_urls_clean.txt", help="Output file for filtered URLs")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kept_urls: list[str] = []
    stats: list[tuple[str, int, int]] = []

    for file_path in sorted(input_dir.glob("*.txt")):
        raw_count = 0
        kept_count = 0

        for url in read_urls_from_file(file_path):
            raw_count += 1
            cleaned = normalize_url(url)
            if is_probably_recipe_url(cleaned):
                kept_urls.append(cleaned)
                kept_count += 1

        stats.append((file_path.name, raw_count, kept_count))

    seen: set[str] = set()
    unique_urls: list[str] = []
    for url in kept_urls:
        if url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)

    output_path.write_text("\n".join(unique_urls), encoding="utf-8")

    print("\nFILTER REPORT")
    print("=" * 60)
    for name, raw_count, kept_count in stats:
        print(f"{name:35} raw={raw_count:6} kept={kept_count:6}")
    print("=" * 60)
    print(f"Total kept : {len(unique_urls)}")
    print(f"Saved to   : {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()