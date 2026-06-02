
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .raw_record import RawRecord
from .source_adapter import SourceAdapter

try:
    import whisper
except Exception:
    whisper = None


class AudioRecipeAdapter(SourceAdapter):
    """
    DS4 — Audio adapter.

    Reads .mp3 / .wav files, transcribes them with Whisper, and emits RawRecord objects.
    """

    def __init__(
        self,
        source_id: str,
        source_type: str = "audio",
        version: str = "1.0",
        files: Optional[List[str]] = None,
        file_dir: Optional[str] = None,
        model_name: str = "base",
        language: str = "en",
    ) -> None:
        super().__init__(source_id=source_id, source_type=source_type, version=version)
        self.files = files or []
        self.file_dir = file_dir
        self.model_name = model_name
        self.language = language
        self.errors: List[Dict[str, Any]] = []
        self._model = None

    def validate_config(self) -> None:
        if not self.files and not self.file_dir:
            raise ValueError("AudioRecipeAdapter requires either files or file_dir")

        if whisper is None:
            raise ImportError(
                "openai-whisper is not available. Install it with: pip install openai-whisper"
            )

        if self.file_dir:
            path = Path(self.file_dir)
            if not path.exists():
                raise FileNotFoundError(f"Audio folder not found: {path}")

    def _load_files(self) -> List[Path]:
        if self.files:
            return [Path(f) for f in self.files if str(f).strip()]

        if self.file_dir:
            path = Path(self.file_dir)
            return [
                p for p in path.iterdir()
                if p.is_file() and p.suffix.lower() in {".mp3", ".wav", ".m4a", ".flac"}
            ]

        return []

    def _get_model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_name)
        return self._model

    def extract(self) -> List[RawRecord]:
        self.validate_config()
        self.errors = []

        records: List[RawRecord] = []
        model = self._get_model()

        for file_path in self._load_files():
            try:
                if not file_path.exists():
                    raise FileNotFoundError(f"Audio file not found: {file_path}")

                result = model.transcribe(str(file_path), language=self.language)
                transcript = (result.get("text") or "").strip()

                parsed = self._parse_transcript(transcript)

                record = RawRecord(
                    source_id=self.source_id,
                    source_type=self.source_type,
                    version=self.version,
                    raw_content={
                        "title": file_path.stem.replace("_", " ").strip() or "Untitled Audio Recipe",
                        "source_url": str(file_path),
                        "audio_file": str(file_path),
                        "transcript": transcript,
                        "ingredients": parsed["ingredients"],
                        "steps": parsed["steps"],
                    },
                    metadata={
                        "adapter": "AudioRecipeAdapter",
                        "language": self.language,
                        "model_name": self.model_name,
                        "transcript_source": "whisper",
                    },
                )
                records.append(record)

            except Exception as exc:
                self.errors.append(
                    {
                        "file": str(file_path),
                        "source_id": self.source_id,
                        "error": str(exc),
                    }
                )

        return records

    def _parse_transcript(self, transcript: str) -> Dict[str, List[str]]:
        if not transcript:
            return {"ingredients": [], "steps": []}

        lines = [line.strip() for line in transcript.splitlines() if line.strip()]

        ingredients: List[str] = []
        steps: List[str] = []

        in_ingredients = False
        in_steps = False

        for line in lines:
            lower = line.lower()

            if lower in {"ingredients", "ingredient list"} or lower.startswith("ingredients:"):
                in_ingredients = True
                in_steps = False
                continue

            if lower in {"steps", "instructions", "method", "directions"} or lower.startswith("steps:"):
                in_steps = True
                in_ingredients = False
                continue

            if in_ingredients:
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

    def _guess_ingredients(self, lines: List[str]) -> List[str]:
        found: List[str] = []
        for line in lines:
            text = line.lower()
            if any(unit in text for unit in ["cup", "tbsp", "tsp", "gram", "ml", "kg", "pinch", "clove"]):
                found.append(line)
        return found

    def _guess_steps(self, lines: List[str]) -> List[str]:
        return lines[:30]

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