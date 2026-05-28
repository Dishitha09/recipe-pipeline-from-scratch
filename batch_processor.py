from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from deduplication.deduplicate import deduplicate_recipes
from enrichment.enrich_recipe import enrich_recipe
from ingestion.json_adapter import JSONRecipeAdapter
from normalization.normalize_recipe import normalize_recipe
from parsing.ingredient_parser import parse_ingredient_list
from preprocessing.coerce import coerce_raw_record
from utils.logging_config import get_logger
from validation.validator import validate_recipe


RAW_DIR = Path("data/raw")
ACCEPTED_OUTPUT = Path("processed_data/accepted_recipes.json")
REJECTED_OUTPUT = Path("quarantine/rejected_recipes.json")

logger = get_logger("batch_processor")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_existing_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def process_raw_record(raw_record) -> Dict[str, Any]:
    preprocessed = coerce_raw_record(raw_record.raw_content)
    parsed_ingredients = parse_ingredient_list(preprocessed.ingredients)

    pipeline_recipe = {
        "title": preprocessed.title,
        "cuisine": preprocessed.cuisine,
        "prep_time": preprocessed.prep_time,
        "servings": preprocessed.servings,
        "steps": preprocessed.steps,
        "ingredients": parsed_ingredients,
        "metadata": preprocessed.metadata,
        "source_id": raw_record.source_id,
        "source_type": raw_record.source_type,
        "record_id": raw_record.record_id,
        "ingested_at": raw_record.ingested_at,
    }

    enriched = enrich_recipe(pipeline_recipe)
    normalized = normalize_recipe(enriched)
    validated = validate_recipe(normalized)

    return {
        "record_id": raw_record.record_id,
        "source_id": raw_record.source_id,
        "source_type": raw_record.source_type,
        "ingested_at": raw_record.ingested_at,
        "verdict": validated["verdict"],
        "recipe": validated["recipe"],
        "check_results": validated["check_results"],
    }


def process_source_file(file_path: Path) -> Dict[str, int]:
    logger.info("Processing source file: %s", file_path)

    adapter = JSONRecipeAdapter(str(file_path))
    raw_records = adapter.extract()

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for raw_record in raw_records:
        try:
            output_row = process_raw_record(raw_record)

            if output_row["verdict"] == "ACCEPTED":
                accepted.append(output_row)
                logger.info("Accepted record_id=%s", raw_record.record_id)
            else:
                rejected.append(output_row)
                logger.warning(
                    "Rejected record_id=%s verdict=%s",
                    raw_record.record_id,
                    output_row["verdict"],
                )

        except Exception as exc:
            logger.exception("Error processing record_id=%s", raw_record.record_id)
            rejected.append(
                {
                    "record_id": raw_record.record_id,
                    "source_id": raw_record.source_id,
                    "source_type": raw_record.source_type,
                    "ingested_at": raw_record.ingested_at,
                    "verdict": "ERROR",
                    "error": str(exc),
                    "raw_content": raw_record.raw_content,
                    "source_file": str(file_path),
                }
            )

    return {
        "total": len(raw_records),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "accepted_rows": accepted,
        "rejected_rows": rejected,
    }


def find_source_files() -> List[Path]:
    if not RAW_DIR.exists():
        return []

    files = sorted(RAW_DIR.glob("*_recipes.json"))

    return [
        path
        for path in files
        if path.name != "web_recipes.json"
    ]


def main() -> None:
    source_files = find_source_files()

    if not source_files:
        logger.warning("No source files found in %s", RAW_DIR)
        print({"total_files": 0, "total": 0, "accepted": 0, "rejected": 0})
        return

    all_accepted: List[Dict[str, Any]] = []
    all_rejected: List[Dict[str, Any]] = []

    total = 0

    for file_path in source_files:
        result = process_source_file(file_path)

        total += result["total"]
        all_accepted.extend(result["accepted_rows"])
        all_rejected.extend(result["rejected_rows"])

    logger.info("Running deduplication on %d accepted recipes", len(all_accepted))

    unique_recipes, duplicate_recipes = deduplicate_recipes(
        [row["recipe"] for row in all_accepted]
    )

    deduped_accepted: List[Dict[str, Any]] = []
    seen = set()

    for row in all_accepted:
        fingerprint = json.dumps(row["recipe"], sort_keys=True, ensure_ascii=False)
        if row["recipe"] in unique_recipes and fingerprint not in seen:
            deduped_accepted.append(row)
            seen.add(fingerprint)

    ensure_parent(ACCEPTED_OUTPUT)
    ensure_parent(REJECTED_OUTPUT)

    ACCEPTED_OUTPUT.write_text(
        json.dumps(
            load_existing_json(ACCEPTED_OUTPUT, []) + deduped_accepted,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    REJECTED_OUTPUT.write_text(
        json.dumps(
            load_existing_json(REJECTED_OUTPUT, []) + all_rejected,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = {
        "total_files": len(source_files),
        "total": total,
        "accepted": len(deduped_accepted),
        "rejected": len(all_rejected),
        "duplicates_removed": len(duplicate_recipes),
    }

    logger.info("Batch summary: %s", summary)
    print(summary)


if __name__ == "__main__":
    main()