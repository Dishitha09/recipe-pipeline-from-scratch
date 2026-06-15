from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PIL import Image
import pytesseract

from .raw_record import RawRecord
from .source_adapter import SourceAdapter


# Windows Tesseract location
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class ImageRecipeAdapter(SourceAdapter):

    def __init__(
        self,
        source_id: str,
        source_type: str = "image",
        version: str = "1.0",
        file_dir: str = "data/raw/images",
    ):
        super().__init__(
            source_id,
            source_type,
            version,
        )

        self.file_dir = file_dir
        self.errors: List[Dict[str, Any]] = []

    def validate_config(self):

        path = Path(self.file_dir)

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def extract(self) -> List[RawRecord]:

        self.validate_config()

        image_dir = Path(
            self.file_dir
        )

        records = []

        for image_file in image_dir.glob("*"):

            if image_file.suffix.lower() not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            ]:
                continue

            try:

                image = Image.open(
                    image_file
                )

                ocr_text = (
                    pytesseract.image_to_string(
                        image
                    )
                    .strip()
                )

                records.append(
                    RawRecord(
                        source_id=self.source_id,
                        source_type=self.source_type,
                        version=self.version,
                        raw_content={
                            "title": image_file.stem,
                            "image_path": str(
                                image_file
                            ),
                            "ocr_text": ocr_text,
                        },
                        metadata={
                            "adapter": "ImageRecipeAdapter",
                            "ocr_enabled": True,
                            "ocr_length": len(
                                ocr_text
                            ),
                        },
                    )
                )

            except Exception as exc:

                self.errors.append(
                    {
                        "file": str(
                            image_file
                        ),
                        "error": str(exc),
                    }
                )

        return records