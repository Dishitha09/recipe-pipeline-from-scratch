from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber

from .raw_record import RawRecord
from .source_adapter import SourceAdapter


class PDFRecipeAdapter(SourceAdapter):
    """
    DS5 — PDF adapter.

    Reads recipe PDFs, extracts text with pdfplumber, and emits RawRecord objects.
    Scanned PDFs without extractable text will raise an error for now.
    """

    def __init__(
        self,
        source_id: str,
        source_type: str = "pdf",
        version: str = "1.0",
        files: Optional[List[str]] = None,
        file_dir: Optional[str] = None,
    ) -> None:
        super().__init__(source_id=source_id, source_type=source_type, version=version)
        self.files = files or []
        self.file_dir = file_dir
        self.errors: List[Dict[str, Any]] = []

    def validate_config(self) -> None:
        if not self.files and not self.file_dir:
            raise ValueError("PDFRecipeAdapter requires either files or file_dir")

        if self.file_dir:
            path = Path(self.file_dir)
            if not path.exists():
                raise FileNotFoundError(f"PDF folder not found: {path}")

    def _load_files(self) -> List[Path]:
        if self.files:
            return [Path(f) for f in self.files if str(f).strip()]

        if self.file_dir:
            path = Path(self.file_dir)
            return [
                p for p in path.iterdir()
                if p.is_file() and p.suffix.lower() == ".pdf"
            ]

        return []

    def extract(self) -> List[RawRecord]:
        self.validate_config()
        self.errors = []

        records: List[RawRecord] = []

        for pdf_path in self._load_files():
            try:
                if not pdf_path.exists():
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")

                full_text, page_count = self._extract_text(pdf_path)

                if not full_text.strip():
                    raise ValueError("No extractable text found in PDF (scanned OCR not enabled yet)")

                parsed = self._parse_text(full_text)

                title = self._guess_title(pdf_path, full_text)

                record = RawRecord(
                    source_id=self.source_id,
                    source_type=self.source_type,
                    version=self.version,
                    raw_content={
                        "title": title,
                        "source_url": str(pdf_path),
                        "pdf_file": str(pdf_path),
                        "page_count": page_count,
                        "text": full_text,
                        "ingredients": parsed["ingredients"],
                        "steps": parsed["steps"],
                    },
                    metadata={
                        "adapter": "PDFRecipeAdapter",
                        "extraction_engine": "pdfplumber",
                        "page_count": page_count,
                    },
                )
                records.append(record)

            except Exception as exc:
                self.errors.append(
                    {
                        "file": str(pdf_path),
                        "source_id": self.source_id,
                        "error": str(exc),
                    }
                )

        return records

    def _extract_text(self, pdf_path: Path) -> tuple[str, int]:
        page_texts: List[str] = []

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                text = self._cleanup_text(text)
                if text:
                    page_texts.append(text)

            page_count = len(pdf.pages)

        return "\n".join(page_texts).strip(), page_count

    def _cleanup_text(self, text: str) -> str:
        value = str(text).replace("\x00", " ")
        value = value.replace("•", "\n")
        value = value.replace("–", "-").replace("—", "-")
        value = value.replace("\r", "\n")
        value = "\n".join(line.strip() for line in value.splitlines())
        return value.strip()

    def _guess_title(self, pdf_path: Path, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            first = lines[0]
            if 3 <= len(first) <= 120:
                return first

        return pdf_path.stem.replace("_", " ").replace("-", " ").strip() or "Untitled PDF Recipe"

    def _parse_text(self, text: str) -> Dict[str, List[str]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        ingredients: List[str] = []
        steps: List[str] = []

        in_ingredients = False
        in_steps = False

        for line in lines:
            lower = line.lower()

            if self._looks_like_heading(lower, ["ingredients", "ingredient"]):
                in_ingredients = True
                in_steps = False
                continue

            if self._looks_like_heading(lower, ["method", "instructions", "steps", "directions", "procedure"]):
                in_steps = True
                in_ingredients = False
                continue

            if in_ingredients:
                if self._looks_like_ingredient_line(line):
                    ingredients.append(line)
                continue

            if in_steps:
                steps.append(line)
                continue

        if not ingredients:
            ingredients = self._guess_ingredients(lines)

        if not steps:
            steps = self._guess_steps(lines)

        return {
            "ingredients": self._dedupe(ingredients),
            "steps": self._dedupe(steps),
        }

    def _looks_like_heading(self, text: str, phrases: List[str]) -> bool:
        t = text.strip().lower()
        return any(t == phrase or t.startswith(phrase + " ") or phrase in t for phrase in phrases)

    def _looks_like_ingredient_line(self, line: str) -> bool:
        text = line.strip().lower()
        if not text:
            return False

        has_quantity = any(ch.isdigit() for ch in text)
        unit_terms = (
            "cup", "cups", "tbsp", "tsp", "teaspoon", "tablespoon",
            "gram", "kg", "ml", "pinch", "clove", "slice", "bowl",
            "handful", "piece", "can", "litre", "liter"
        )
        has_unit = any(term in text for term in unit_terms)

        return has_quantity or has_unit or text.startswith("- ")

    def _guess_ingredients(self, lines: List[str]) -> List[str]:
        return [line for line in lines if self._looks_like_ingredient_line(line)]

    def _guess_steps(self, lines: List[str]) -> List[str]:
        steps = [line for line in lines if not self._looks_like_ingredient_line(line)]
        return steps[:40]

    def _dedupe(self, items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items:
            cleaned = item.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
        return out