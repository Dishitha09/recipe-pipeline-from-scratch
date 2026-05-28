from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "tracking" / "source_registry.json"


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


def add_source(
    source_name: str,
    source_type: str,
    base_url: str,
) -> Dict[str, Any]:
    registry = load_registry()

    existing = next(
        (item for item in registry if item["base_url"] == base_url),
        None,
    )

    if existing:
        return existing

    source = {
        "source_name": source_name,
        "source_type": source_type,
        "base_url": base_url,
        "status": "pending",
        "recipes_scraped": 0,
        "last_scraped_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": "",
    }

    registry.append(source)
    save_registry(registry)
    return source


def update_source_status(
    base_url: str,
    status: str,
    recipes_scraped: int | None = None,
    notes: str | None = None,
) -> Dict[str, Any]:
    registry = load_registry()

    for source in registry:
        if source["base_url"] == base_url:
            source["status"] = status
            source["last_scraped_at"] = datetime.now(timezone.utc).isoformat()

            if recipes_scraped is not None:
                source["recipes_scraped"] = recipes_scraped

            if notes is not None:
                source["notes"] = notes

            save_registry(registry)
            return source

    raise ValueError(f"Source not found: {base_url}")


def get_summary() -> Dict[str, Any]:
    registry = load_registry()

    return {
        "total_sources": len(registry),
        "completed_sources": sum(1 for item in registry if item["status"] == "completed"),
        "failed_sources": sum(1 for item in registry if item["status"] == "failed"),
        "pending_sources": sum(1 for item in registry if item["status"] == "pending"),
        "total_recipes_scraped": sum(item.get("recipes_scraped", 0) for item in registry),
    }


if __name__ == "__main__":
    print(get_summary())