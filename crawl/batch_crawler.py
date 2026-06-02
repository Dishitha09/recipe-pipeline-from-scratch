from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ps1.web_adapter import WebScraperAdapter

from .crawl_queue import CrawlQueue
from .url_discovery import discover_urls, load_urls_from_file


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def crawl_one(url: str, source_id: str, source_type: str = "web") -> Tuple[Optional[dict], Optional[str], int]:
    adapter = WebScraperAdapter(source_id=source_id, source_type=source_type, urls=[url], timeout=20)
    records = adapter.extract()
    errors = getattr(adapter, "errors", [])

    if records:
        return records[0].to_dict(), None, 200

    error_text = errors[0]["error"] if errors else "No record extracted"
    return None, error_text, 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch crawl a large recipe URL queue.")
    parser.add_argument("--queue-db", default="data/registry.db")
    parser.add_argument("--source-id", default="ds2_batch_web")
    parser.add_argument("--source-name", default="Batch Web Crawl")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-urls", type=int, default=10000)
    parser.add_argument("--output-dir", default="runs/crawl_batches")
    parser.add_argument("--url-file", action="append", default=[])
    parser.add_argument("--sitemap", action="append", default=[])
    parser.add_argument("--seed", action="append", default=[])
    parser.add_argument("--allow-domain", action="append", default=[])
    args = parser.parse_args()

    queue = CrawlQueue(args.queue_db)

    discovered = discover_urls(
        url_files=args.url_file,
        sitemap_urls=args.sitemap,
        html_seed_urls=args.seed,
        allowed_domains=args.allow_domain,
        max_urls=args.max_urls,
    )

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

        batch_no += 1
        print(f"\nBatch {batch_no}: claimed {len(batch)} URLs")

        batch_records: List[Dict[str, Any]] = []
        batch_failures: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_map = {
                executor.submit(crawl_one, row["url"], args.source_id, row.get("source_type", "web")): row
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
                        queue.mark_failed(queue_id, error_text, http_status=http_status)
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