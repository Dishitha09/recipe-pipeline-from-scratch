from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ingestion.json_adapter import JSONRecipeAdapter
from preprocessing.coerce import coerce_raw_record
from parsing.ingredient_parser import parse_ingredient_list
from enrichment.enrich_recipe import enrich_recipe
from normalization.normalize_recipe import normalize_recipe
from validation.validator import validate_recipe
from deduplication.deduplicate import deduplicate_recipes
from utils.logging_config import get_logger


logger = get_logger("pipeline_runner")

INPUT_JSON = Path("data/raw/web_recipes.json")

ACCEPTED_OUTPUT = Path("processed_data/accepted_recipes.json")
REJECTED_OUTPUT = Path("quarantine/rejected_recipes.json")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_existing_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def run_pipeline() -> Dict[str, int]:
    logger.info("Starting pipeline run")

    adapter = JSONRecipeAdapter(str(INPUT_JSON))

    raw_records = adapter.extract()

    logger.info("Loaded %d raw records", len(raw_records))

    processed_rows: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for raw_record in raw_records:
        try:
            logger.info(
                "Processing record_id=%s",
                raw_record.record_id,
            )

            preprocessed = coerce_raw_record(
                raw_record.raw_content
            )

            parsed_ingredients = parse_ingredient_list(
                preprocessed.ingredients
            )

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

            enriched = enrich_recipe(
                pipeline_recipe
            )

            normalized = normalize_recipe(
                enriched
            )

            validated = validate_recipe(
                normalized
            )

            output_row = {
                "record_id": raw_record.record_id,
                "source_id": raw_record.source_id,
                "source_type": raw_record.source_type,
                "ingested_at": raw_record.ingested_at,
                "verdict": validated["verdict"],
                "recipe": validated["recipe"],
                "check_results": validated["check_results"],
            }

            if validated["verdict"] == "ACCEPTED":
                processed_rows.append(output_row)

                logger.info(
                    "Accepted record_id=%s",
                    raw_record.record_id,
                )

            else:
                rejected.append(output_row)

                logger.warning(
                    "Rejected record_id=%s verdict=%s",
                    raw_record.record_id,
                    validated["verdict"],
                )

        except Exception as exc:
            logger.exception(
                "Error processing record_id=%s",
                raw_record.record_id,
            )

            rejected.append(
                {
                    "record_id": raw_record.record_id,
                    "source_id": raw_record.source_id,
                    "source_type": raw_record.source_type,
                    "ingested_at": raw_record.ingested_at,
                    "verdict": "ERROR",
                    "error": str(exc),
                    "raw_content": raw_record.raw_content,
                }
            )

    logger.info(
        "Running deduplication on %d accepted recipes",
        len(processed_rows),
    )

    unique_recipes, duplicate_recipes = deduplicate_recipes(
        [row["recipe"] for row in processed_rows]
    )

    accepted: List[Dict[str, Any]] = []

    for row in processed_rows:
        if row["recipe"] in unique_recipes:
            accepted.append(row)

    logger.info(
        "Deduplicated %d duplicates",
        len(duplicate_recipes),
    )

    ensure_parent(ACCEPTED_OUTPUT)
    ensure_parent(REJECTED_OUTPUT)

    ACCEPTED_OUTPUT.write_text(
        json.dumps(
            load_existing_json(
                ACCEPTED_OUTPUT,
                [],
            ) + accepted,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    REJECTED_OUTPUT.write_text(
        json.dumps(
            load_existing_json(
                REJECTED_OUTPUT,
                [],
            ) + rejected,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = {
        "total": len(raw_records),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "duplicates_removed": len(duplicate_recipes),
    }

    logger.info(
        "Pipeline summary: %s",
        summary,
    )

    return summary


if __name__ == "__main__":
    summary = run_pipeline()

    print(summary)