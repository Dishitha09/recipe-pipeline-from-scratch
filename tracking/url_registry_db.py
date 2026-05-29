from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "registry.db"
JSON_REGISTRY_PATH = BASE_DIR / "tracking" / "url_registry.json"


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_name TEXT PRIMARY KEY,
                source_type TEXT,
                base_url TEXT,
                status TEXT DEFAULT 'pending',
                recipes_scraped INTEGER DEFAULT 0,
                last_scraped_at TEXT,
                created_at TEXT,
                notes TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                source_name TEXT,
                status TEXT,
                discovered_at TEXT,
                scraped_at TEXT,
                recipe_found INTEGER,
                attempts INTEGER DEFAULT 0,
                last_error TEXT
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_urls_source_name ON urls(source_name)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS crawl_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT,
                started_at TEXT,
                finished_at TEXT,
                status TEXT,
                scraped_count INTEGER DEFAULT 0,
                notes TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS crawl_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                source_name TEXT,
                error TEXT,
                failed_at TEXT,
                context TEXT
            )
            """
        )


def _row_to_dict(row: sqlite3.Row | None) -> Dict[str, Any]:
    return dict(row) if row is not None else {}


def upsert_source(
    source_name: str,
    source_type: Optional[str] = None,
    base_url: Optional[str] = None,
    status: str = "pending",
    recipes_scraped: int = 0,
    last_scraped_at: Optional[str] = None,
    created_at: Optional[str] = None,
    notes: str = "",
) -> Dict[str, Any]:
    initialize_database()

    created_at = created_at or datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM sources WHERE source_name = ?",
            (source_name,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE sources
                SET source_type = COALESCE(?, source_type),
                    base_url = COALESCE(?, base_url),
                    status = ?,
                    recipes_scraped = ?,
                    last_scraped_at = COALESCE(?, last_scraped_at),
                    notes = COALESCE(NULLIF(?, ''), notes)
                WHERE source_name = ?
                """,
                (
                    source_type,
                    base_url,
                    status,
                    recipes_scraped,
                    last_scraped_at,
                    notes,
                    source_name,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO sources (
                    source_name, source_type, base_url, status,
                    recipes_scraped, last_scraped_at, created_at, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_name,
                    source_type,
                    base_url,
                    status,
                    recipes_scraped,
                    last_scraped_at,
                    created_at,
                    notes,
                ),
            )

        row = conn.execute(
            "SELECT * FROM sources WHERE source_name = ?",
            (source_name,),
        ).fetchone()

    return _row_to_dict(row)


def record_url(
    url: str,
    source_name: str,
    discovered_at: Optional[str] = None,
) -> Dict[str, Any]:
    initialize_database()
    url = canonicalize_url(url)
    discovered_at = discovered_at or datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM urls WHERE url = ?",
            (url,),
        ).fetchone()

        if existing:
            if source_name and not existing["source_name"]:
                conn.execute(
                    "UPDATE urls SET source_name = ? WHERE url = ?",
                    (source_name, url),
                )

            row = conn.execute(
                "SELECT * FROM urls WHERE url = ?",
                (url,),
            ).fetchone()
            return _row_to_dict(row)

        conn.execute(
            """
            INSERT INTO urls (
                url, source_name, status, discovered_at,
                scraped_at, recipe_found, attempts, last_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                source_name,
                "discovered",
                discovered_at,
                None,
                None,
                0,
                None,
            ),
        )

        row = conn.execute(
            "SELECT * FROM urls WHERE url = ?",
            (url,),
        ).fetchone()

    return _row_to_dict(row)


def mark_scraped(
    url: str,
    recipe_found: bool,
    error: Optional[str] = None,
    source_name: Optional[str] = None,
) -> Dict[str, Any]:
    initialize_database()
    url = canonicalize_url(url)
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM urls WHERE url = ?",
            (url,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE urls
                SET status = ?,
                    scraped_at = ?,
                    recipe_found = ?,
                    attempts = COALESCE(attempts, 0) + 1,
                    last_error = ?
                WHERE url = ?
                """,
                (
                    "scraped" if recipe_found else "failed",
                    now,
                    1 if recipe_found else 0,
                    error,
                    url,
                ),
            )

            if source_name and not existing["source_name"]:
                conn.execute(
                    "UPDATE urls SET source_name = ? WHERE url = ?",
                    (source_name, url),
                )

        else:
            conn.execute(
                """
                INSERT INTO urls (
                    url, source_name, status, discovered_at,
                    scraped_at, recipe_found, attempts, last_error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url,
                    source_name,
                    "scraped" if recipe_found else "failed",
                    now,
                    now,
                    1 if recipe_found else 0,
                    1,
                    error,
                ),
            )

        row = conn.execute(
            "SELECT * FROM urls WHERE url = ?",
            (url,),
        ).fetchone()

    return _row_to_dict(row)


def record_crawl_run(
    source_name: str,
    started_at: str,
    finished_at: str,
    status: str,
    scraped_count: int,
    notes: str = "",
) -> Dict[str, Any]:
    initialize_database()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO crawl_runs (
                source_name, started_at, finished_at, status, scraped_count, notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source_name,
                started_at,
                finished_at,
                status,
                scraped_count,
                notes,
            ),
        )

        row = conn.execute(
            """
            SELECT * FROM crawl_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return _row_to_dict(row)


def record_failure(
    url: str,
    source_name: Optional[str],
    error: str,
    context: str = "",
) -> Dict[str, Any]:
    initialize_database()
    now = datetime.now(timezone.utc).isoformat()
    url = canonicalize_url(url)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO crawl_failures (
                url, source_name, error, failed_at, context
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                url,
                source_name,
                error,
                now,
                context,
            ),
        )

        row = conn.execute(
            """
            SELECT * FROM crawl_failures
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return _row_to_dict(row)


def migrate_json_registry(json_path: Path | None = None) -> int:
    initialize_database()

    json_path = json_path or JSON_REGISTRY_PATH
    if not json_path.exists():
        return 0

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    migrated = 0

    with get_connection() as conn:
        for row in data:
            if not isinstance(row, dict):
                continue

            url = row.get("url")
            if not url:
                continue

            url = canonicalize_url(url)
            source_name = row.get("source_name")
            status = row.get("status") or "discovered"
            discovered_at = row.get("discovered_at")
            scraped_at = row.get("scraped_at")
            recipe_found = row.get("recipe_found")
            attempts = int(row.get("attempts") or 0)
            last_error = row.get("last_error")

            existing = conn.execute(
                "SELECT * FROM urls WHERE url = ?",
                (url,),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE urls
                    SET source_name = COALESCE(?, source_name),
                        status = ?,
                        discovered_at = COALESCE(?, discovered_at),
                        scraped_at = COALESCE(?, scraped_at),
                        recipe_found = COALESCE(?, recipe_found),
                        attempts = MAX(COALESCE(attempts, 0), ?),
                        last_error = COALESCE(?, last_error)
                    WHERE url = ?
                    """,
                    (
                        source_name,
                        status,
                        discovered_at,
                        scraped_at,
                        1 if recipe_found is True else 0 if recipe_found is False else None,
                        attempts,
                        last_error,
                        url,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO urls (
                        url, source_name, status, discovered_at,
                        scraped_at, recipe_found, attempts, last_error
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        url,
                        source_name,
                        status,
                        discovered_at,
                        scraped_at,
                        1 if recipe_found is True else 0 if recipe_found is False else None,
                        attempts,
                        last_error,
                    ),
                )

            migrated += 1

    return migrated


def get_summary() -> Dict[str, Any]:
    initialize_database()

    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
        discovered = conn.execute(
            "SELECT COUNT(*) FROM urls WHERE status = 'discovered'"
        ).fetchone()[0]
        scraped = conn.execute(
            "SELECT COUNT(*) FROM urls WHERE status = 'scraped'"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM urls WHERE status = 'failed'"
        ).fetchone()[0]
        recipe_found = conn.execute(
            "SELECT COUNT(*) FROM urls WHERE recipe_found = 1"
        ).fetchone()[0]

    return {
        "total_urls": total,
        "discovered": discovered,
        "scraped": scraped,
        "failed": failed,
        "recipe_found": recipe_found,
        "db_path": str(DB_PATH),
    }


def main() -> None:
    initialize_database()
    migrated = migrate_json_registry()

    print(f"Database initialized: {DB_PATH}")
    print(f"Migrated from JSON   : {migrated}")
    print(get_summary())


if __name__ == "__main__":
    main()