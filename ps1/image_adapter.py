from __future__ import annotations

from pathlib import Path
from typing import List

from .raw_record import RawRecord
from .source_adapter import SourceAdapter


class ImageRecipeAdapter(SourceAdapter):

    def __init__(
        self,
        source_id: str,
        source_type: str = "image",
        version: str = "1.0",
        file_dir: str = "data/raw/images",
    ):
        super().__init__(source_id, source_type, version)
        self.file_dir = file_dir

    def validate_config(self):
        Path(self.file_dir).mkdir(parents=True, exist_ok=True)

    def extract(self) -> List[RawRecord]:

        image_dir = Path(self.file_dir)

        records = []

        for image_file in image_dir.glob("*"):

            if image_file.suffix.lower() not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            ]:
                continue

            records.append(
                RawRecord(
                    source_id=self.source_id,
                    source_type=self.source_type,
                    version=self.version,
                    raw_content={
                        "title": image_file.stem,
                        "image_path": str(image_file),
                        "ocr_text": "",
                    },
                    metadata={
                        "adapter": "ImageRecipeAdapter"
                    },
                )
            )

        return records