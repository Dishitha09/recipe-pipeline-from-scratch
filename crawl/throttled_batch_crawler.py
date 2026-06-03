from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ps1.web_adapter import WebScraperAdapter

from .crawl_queue import CrawlQueue
from .url_discovery import discover_urls


DOMAIN_LOCK = Lock()
DOMAIN_NEXT_ALLOWED: dict[str, float] = defaultdict(float)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _domain_of(url: str) -> str:
    return urlparse(url).netloc.lower()


def _domain_matches(host: str, domain: str) -> bool:
    host = host.lower()
    domain = domain.lower().lstrip(".")
    return host == domain or host.endswith("." + domain)


def _allowed_by_domain(
    url: str,
    only_domains: List[str],
    exclude_domains: List[str],
) -> bool:
    host = _domain_of(url)

    if only_domains:
        if not any(_domain_matches(host, d) for d in only_domains):
            return False

    if exclude_domains:
        if any(_domain_matches(host, d) for d in exclude_domains):
            return False

    return True


def _wait_for_turn(domain: str, delay_seconds: float) -> None:
    if delay_seconds <= 0:
        return

    with DOMAIN_LOCK:
        now = time.monotonic()
        next_allowed = DOMAIN_NEXT_ALLOWED[domain]
        wait_for = max(0.0, next_allowed - now)
        DOMAIN_NEXT_ALLOWED[domain] = max(now, next_allowed) + delay_seconds

    if wait_for > 0:
        time.sleep(wait_for + random.uniform(0.05, 0.35))


def _is_rate_limit_error(text: str) -> bool:
    value = text.lower()
    return (
        "429" in value
        or "too many requests" in value
        or "rate limit" in value
        or "temporarily blocked" in value
    )


def crawl_one(
    url: str,
    source_id: str,
    source_type: str = "web",
    timeout: int = 20,
    retries: int = 3,
    default_delay: float = 1.0,
    slow_domains: Optional[List[str]] = None,
    slow_seconds: float = 5.0,
) -> Tuple[Optional[dict], Optional[str], int]:
    domain = _domain_of(url)
    slow_domains = slow_domains or []

    delay = slow_seconds if any(_domain_matches(domain, d) for d in slow_domains) else default_delay

    last_error: Optional[str] = None

    for attempt in range(retries + 1):
        try:
            _wait_for_turn(domain, delay)

            adapter = WebScraperAdapter(
                source_id=source_id,
                source_type=source_type,
                urls=[url],
                timeout=timeout,
            )
            records = adapter.extract()
            errors = getattr(adapter, "errors", []) or []

            if records:
                record = records[0]
                return record.to_dict(), None, 200

            if errors:
                first_error = errors[0]
                if isinstance(first_error, dict):
                    last_error = str(first_error.get("error", "No record extracted"))
                else:
                    last_error = str(first_error)

                if _is_rate_limit_error(last_error) and attempt < retries:
                    backoff = (2 ** attempt) * delay
                    time.sleep(backoff + random.uniform(0.1, 0.5))
                    continue

                return None, last_error, 0

            return None, "No record extracted", 0

        except Exception as exc:
            last_error = str(exc)
            if _is_rate_limit_error(last_error) and attempt < retries:
                backoff = (2 ** attempt) * delay
                time.sleep(backoff + random.uniform(0.1, 0.5))
                continue
            return None, last_error, 0

    return None, last_error or "Unknown error", 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Throttle-aware batch crawler for recipe URLs.")
    parser.add_argument("--queue-db", default="data/registry.db")
    parser.add_argument("--source-id", default="ds2_batch_web")
    parser.add_argument("--source-name", default="Batch Web Crawl")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--max-urls", type=int, default=500)
    parser.add_argument("--output-dir", default="runs/crawl_batches")
    parser.add_argument("--url-file", action="append", default=[])
    parser.add_argument("--sitemap", action="append", default=[])
    parser.add_argument("--seed", action="append", default=[])
    parser.add_argument("--allow-domain", action="append", default=[])
    parser.add_argument("--only-domain", action="append", default=[])
    parser.add_argument("--exclude-domain", action="append", default=[])
    parser.add_argument("--default-delay", type=float, default=1.0)
    parser.add_argument("--slow-domain", action="append", default=[])
    parser.add_argument("--slow-seconds", type=float, default=5.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    queue = CrawlQueue(args.queue_db)

    discovered = discover_urls(
        url_files=args.url_file,
        sitemap_urls=args.sitemap,
        html_seed_urls=args.seed,
        allowed_domains=args.allow_domain,
        max_urls=args.max_urls,
    )

    if args.only_domain or args.exclude_domain:
        discovered = [
            u for u in discovered
            if _allowed_by_domain(u, args.only_domain, args.exclude_domain)
        ]

    if discovered:
        inserted = queue.enqueue_many(discovered, source_name=args.source_name, source_type="web")
        print(f"Discovered URLs: {len(discovered)}")
        print(f"Queued new URLs : {inserted}")
    else:
        print("No URLs discovered from discovery inputs.")
        print("Proceeding with existing queue items, if any.")

    run_dir = Path(args.output_dir) / f"run_{_utc_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    all_records: List[Dict[str, Any]] = []
    all_failures: List[Dict[str, Any]] = []
    batch_no = 0
    processed_total = 0

    while processed_total < args.max_urls:
        batch = queue.claim_batch(limit=args.batch_size)
        if not batch:
            break

        if args.only_domain or args.exclude_domain:
            batch = [
                row for row in batch
                if _allowed_by_domain(
                    row["url"],
                    args.only_domain,
                    args.exclude_domain,
                )
            ]

        if not batch:
            continue

        batch_no += 1
        print(f"\nBatch {batch_no}: claimed {len(batch)} URLs")

        batch_records: List[Dict[str, Any]] = []
        batch_failures: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_map = {
                executor.submit(
                    crawl_one,
                    row["url"],
                    args.source_id,
                    row.get("source_type", "web"),
                    args.timeout,
                    args.retries,
                    args.default_delay,
                    args.slow_domain,
                    args.slow_seconds,
                ): row
                for row in batch
            }

            for future in as_completed(future_map):
                row = future_map[future]
                queue_id = int(row["queue_id"])
                url = row["url"]

                try:
                    record, error_text, http_status = future.result()
                    if record is not None:
                        batch_records.append(record)
                        queue.mark_done(queue_id, http_status=http_status, result_path=str(run_dir / "records.json"))
                    else:
                        failure = {"queue_id": queue_id, "url": url, "error": error_text}
                        batch_failures.append(failure)
                        queue.mark_failed(queue_id, error_text or "Unknown error", http_status=http_status)
                except Exception as exc:
                    failure = {"queue_id": queue_id, "url": url, "error": str(exc)}
                    batch_failures.append(failure)
                    queue.mark_failed(queue_id, str(exc))

        processed_total += len(batch)
        all_records.extend(batch_records)
        all_failures.extend(batch_failures)

        _write_json(run_dir / f"records_batch_{batch_no}.json", batch_records)
        _write_json(run_dir / f"failures_batch_{batch_no}.json", batch_failures)

        print(f"  records ok   : {len(batch_records)}")
        print(f"  records fail : {len(batch_failures)}")
        print(f"  queue stats  : {queue.stats()}")

    _write_json(run_dir / "records.json", all_records)
    _write_json(run_dir / "failures.json", all_failures)
    _write_json(
        run_dir / "manifest.json",
        {
            "run_dir": str(run_dir),
            "processed_total": processed_total,
            "records_ok": len(all_records),
            "records_failed": len(all_failures),
            "queue_stats": queue.stats(),
            "source_id": args.source_id,
            "source_name": args.source_name,
        },
    )

    print("\n" + "=" * 50)
    print("BATCH CRAWL COMPLETE")
    print("=" * 50)
    print(f"Processed total : {processed_total}")
    print(f"Records saved   : {len(all_records)}")
    print(f"Failures saved  : {len(all_failures)}")
    print(f"Run directory   : {run_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()