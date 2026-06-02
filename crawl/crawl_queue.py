from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_url(url: str) -> str:
    value = str(url).strip()
    if not value:
        return ""

    if not urlparse(value).scheme:
        value = "https://" + value.lstrip("/")

    parsed = urlparse(value)
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    fragment = ""

    return urlunparse((scheme, netloc, path, parsed.params, query, fragment))


class CrawlQueue:
    def __init__(self, db_path: str | Path = "data/registry.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_queue (
                    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    normalized_url TEXT NOT NULL UNIQUE,
                    source_name TEXT,
                    source_type TEXT NOT NULL DEFAULT 'web',
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER NOT NULL DEFAULT 0,
                    discovered_at TEXT NOT NULL,
                    claimed_at TEXT,
                    finished_at TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    last_http_status INTEGER,
                    result_path TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_queue_status_priority
                ON crawl_queue(status, priority DESC, discovered_at ASC)
                """
            )
            conn.commit()

    def enqueue(
        self,
        url: str,
        source_name: str | None = None,
        source_type: str = "web",
        priority: int = 0,
    ) -> bool:
        cleaned = str(url).strip()
        if not cleaned:
            return False

        normalized = normalize_url(cleaned)
        if not normalized:
            return False

        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO crawl_queue (
                        url, normalized_url, source_name, source_type,
                        status, priority, discovered_at, attempts
                    )
                    VALUES (?, ?, ?, ?, 'pending', ?, ?, 0)
                    """,
                    (
                        cleaned,
                        normalized,
                        source_name,
                        source_type,
                        int(priority),
                        _utc_now(),
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def enqueue_many(
        self,
        urls: Iterable[str],
        source_name: str | None = None,
        source_type: str = "web",
        priority: int = 0,
    ) -> int:
        inserted = 0
        for url in urls:
            if self.enqueue(url, source_name=source_name, source_type=source_type, priority=priority):
                inserted += 1
        return inserted

    def pending_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM crawl_queue WHERE status = 'pending'"
            ).fetchone()
            return int(row["cnt"]) if row else 0

    def claim_batch(self, limit: int = 50) -> List[dict[str, Any]]:
        limit = max(1, int(limit))

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """
                SELECT queue_id, url, normalized_url, source_name, source_type, status,
                       priority, discovered_at, claimed_at, finished_at, attempts,
                       last_error, last_http_status, result_path
                FROM crawl_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, discovered_at ASC, queue_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            ids = [row["queue_id"] for row in rows]
            if ids:
                placeholders = ",".join("?" for _ in ids)
                conn.execute(
                    f"""
                    UPDATE crawl_queue
                    SET status = 'running',
                        claimed_at = ?,
                        attempts = attempts + 1
                    WHERE queue_id IN ({placeholders})
                    """,
                    [_utc_now(), *ids],
                )
                conn.commit()
            else:
                conn.commit()

        return [dict(row) for row in rows]

    def mark_done(
        self,
        queue_id: int,
        http_status: int | None = None,
        result_path: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE crawl_queue
                SET status = 'done',
                    finished_at = ?,
                    last_http_status = COALESCE(?, last_http_status),
                    result_path = COALESCE(?, result_path)
                WHERE queue_id = ?
                """,
                (_utc_now(), http_status, result_path, queue_id),
            )
            conn.commit()

    def mark_failed(
        self,
        queue_id: int,
        error: str,
        http_status: int | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE crawl_queue
                SET status = 'failed',
                    finished_at = ?,
                    last_error = ?,
                    last_http_status = COALESCE(?, last_http_status)
                WHERE queue_id = ?
                """,
                (_utc_now(), error, http_status, queue_id),
            )
            conn.commit()

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS cnt
                FROM crawl_queue
                GROUP BY status
                """
            ).fetchall()

        out = {"pending": 0, "running": 0, "done": 0, "failed": 0}
        for row in rows:
            out[str(row["status"])] = int(row["cnt"])
        return out