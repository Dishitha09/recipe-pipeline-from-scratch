from __future__ import annotations

import json
import time
from pathlib import Path

from ps1.registry import SourceRegistry

from ps1.metrics import (
    increment,
    get_metrics,
)

REGISTRY_FILE = Path(__file__).with_name(
    "source_registry.yaml"
)

OUTPUT_FILE = Path(__file__).with_name(
    "raw_records.json"
)

ERRORS_FILE = Path(__file__).with_name(
    "adapter_errors.json"
)


def main() -> None:

    registry = SourceRegistry(
        REGISTRY_FILE
    )

    adapters = registry.load_adapters()

    all_records: list[dict] = []
    all_errors: list[dict] = []

    print(
        f"Loaded {len(adapters)} adapter(s) from registry."
    )

    for adapter in adapters:

        print(
            f"\nRunning {adapter.source_id} ({adapter.__class__.__name__}) ..."
        )

        start_time = time.time()

        try:

            records = adapter.extract()

            runtime = round(
                time.time() - start_time,
                2,
            )

            all_records.extend(
                [
                    record.to_dict()
                    for record in records
                ]
            )

            errors = getattr(
                adapter,
                "errors",
                [],
            )

            all_errors.extend(errors)

            increment(
                "records_processed",
                len(records),
            )

            increment(
                "records_failed",
                len(errors),
            )

            print(
                f"  records extracted : {len(records)}"
            )

            print(
                f"  adapter errors    : {len(errors)}"
            )

            print(
                f"  runtime (sec)     : {runtime}"
            )

        except Exception as exc:

            increment(
                "adapter_failures"
            )

            error = {
                "source_id": adapter.source_id,
                "source_type": adapter.source_type,
                "error": str(exc),
            }

            all_errors.append(error)

            print(
                f"  FAILED: {exc}"
            )

    OUTPUT_FILE.write_text(
        json.dumps(
            all_records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    ERRORS_FILE.write_text(
        json.dumps(
            all_errors,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 50)
    print("PS-1 RUN COMPLETE")
    print("=" * 50)

    print(
        f"Total records   : {len(all_records)}"
    )

    print(
        f"Total errors    : {len(all_errors)}"
    )

    print(
        f"Records file    : {OUTPUT_FILE}"
    )

    print(
        f"Errors file     : {ERRORS_FILE}"
    )

    print("\nMETRICS")
    print(
        get_metrics()
    )

    print("=" * 50)


if __name__ == "__main__":
    main()