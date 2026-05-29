from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit


BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "tracking" / "url_registry.json"


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    clean_parts = parts._replace(fragment="")
    return urlunsplit(clean_parts)


def load_registry() -> List[Dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        return []

    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_registry(data: List[Dict[str, Any]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def record_url(
    url: str,
    source_name: str,
    discovered_at: Optional[str] = None,
) -> Dict[str, Any]:
    url = canonicalize_url(url)
    registry = load_registry()

    existing = next((item for item in registry if item["url"] == url), None)
    if existing:
        return existing

    row = {
        "url": url,
        "source_name": source_name,
        "status": "discovered",
        "discovered_at": discovered_at or datetime.now(timezone.utc).isoformat(),
        "scraped_at": None,
        "recipe_found": None,
        "attempts": 0,
        "last_error": None,
    }

    registry.append(row)
    save_registry(registry)
    return row


def mark_scraped(
    url: str,
    recipe_found: bool,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    url = canonicalize_url(url)
    registry = load_registry()

    for item in registry:
        if item["url"] == url:
            item["status"] = "scraped" if recipe_found else "failed"
            item["scraped_at"] = datetime.now(timezone.utc).isoformat()
            item["recipe_found"] = recipe_found
            item["attempts"] = int(item.get("attempts", 0)) + 1
            item["last_error"] = error
            save_registry(registry)
            return item

    row = {
        "url": url,
        "source_name": None,
        "status": "scraped" if recipe_found else "failed",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "recipe_found": recipe_found,
        "attempts": 1,
        "last_error": error,
    }
    registry.append(row)
    save_registry(registry)
    return row


def get_summary() -> Dict[str, Any]:
    registry = load_registry()

    return {
        "total_urls": len(registry),
        "discovered": sum(1 for item in registry if item["status"] == "discovered"),
        "scraped": sum(1 for item in registry if item["status"] == "scraped"),
        "failed": sum(1 for item in registry if item["status"] == "failed"),
    }


if __name__ == "__main__":
    print(get_summary())