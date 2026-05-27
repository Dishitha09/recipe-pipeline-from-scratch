import csv
from typing import List

from ingestion.base_adapter import SourceAdapter
from ingestion.raw_record import RawRecord


class CSVRecipeAdapter(SourceAdapter):

    def __init__(self, file_path: str):
        self.file_path = file_path

    def validate_config(self):

        if not self.file_path.endswith(".csv"):
            raise ValueError("Invalid CSV file")

    def extract(self) -> List[RawRecord]:

        self.validate_config()

        records = []

        with open(self.file_path, mode="r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                record = RawRecord(
                    source_id="kaggle_csv",
                    source_type="csv",
                    raw_content=row
                )

                records.append(record)

        return records