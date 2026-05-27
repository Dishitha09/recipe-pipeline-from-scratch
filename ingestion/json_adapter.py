import json
from typing import List

from ingestion.base_adapter import SourceAdapter
from ingestion.raw_record import RawRecord


class JSONRecipeAdapter(SourceAdapter):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def validate_config(self):
        if not self.file_path.endswith(".json"):
            raise ValueError("Invalid JSON file")

    def extract(self) -> List[RawRecord]:
        self.validate_config()

        with open(self.file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        recipes = payload.get("recipes", []) if isinstance(payload, dict) else payload

        records: List[RawRecord] = []

        for item in recipes:
            record = RawRecord(
                source_id=item.get("source_id", "web"),
                source_type=item.get("source_type", "web"),
                raw_content=item,
            )
            records.append(record)

        return records