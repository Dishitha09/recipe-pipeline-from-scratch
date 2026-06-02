from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from .raw_record import RawRecord
from .source_adapter import SourceAdapter


class YouTubeRecipeAdapter(SourceAdapter):
    """
    DS3 — YouTube adapter.

    This adapter:
    - reads YouTube URLs from urls or url_file
    - uses yt-dlp to fetch metadata
    - uses youtube-transcript-api to fetch transcripts when available
    - performs lightweight transcript parsing into ingredients and steps
    - emits RawRecord objects
    """

    def __init__(
        self,
        source_id: str,
        source_type: str = "youtube",
        version: str = "1.0",
        urls: Optional[List[str]] = None,
        url_file: Optional[str] = None,
        timeout: int = 20,
        user_agent: str = "Mozilla/5.0",
        transcript_languages: Optional[List[str]] = None,
    ) -> None:
        super().__init__(source_id=source_id, source_type=source_type, version=version)
        self.urls = urls or []
        self.url_file = url_file
        self.timeout = timeout
        self.user_agent = user_agent
        self.transcript_languages = transcript_languages or ["en"]
        self.errors: List[Dict[str, Any]] = []

    def validate_config(self) -> None:
        if not self.urls and not self.url_file:
            raise ValueError("YouTubeRecipeAdapter requires either urls or url_file")

        if self.url_file:
            from pathlib import Path

            path = Path(self.url_file)
            if not path.exists():
                raise FileNotFoundError(f"URL file not found: {path}")

    def _load_urls(self) -> List[str]:
        if self.urls:
            return [u.strip() for u in self.urls if str(u).strip()]

        if self.url_file:
            from pathlib import Path

            path = Path(self.url_file)
            lines = path.read_text(encoding="utf-8").splitlines()
            return [line.strip() for line in lines if line.strip()]

        return []

    def extract(self) -> List[RawRecord]:
        self.validate_config()
        self.errors = []

        records: List[RawRecord] = []

        for url in self._load_urls():
            try:
                info = self._extract_video_info(url)
                video_id = info.get("id") or self._video_id_from_url(url)
                title = self._first_non_empty(
                    info.get("title"),
                    self._title_from_url(url),
                    "Untitled YouTube Recipe",
                )

                transcript_text, transcript_source = self._get_transcript_text(
                    video_id=video_id,
                    fallback_text=info.get("description", ""),
                )

                parsed = self._parse_transcript(transcript_text)

                record = RawRecord(
                    source_id=self.source_id,
                    source_type=self.source_type,
                    version=self.version,
                    raw_content={
                        "title": title,
                        "source_url": url,
                        "video_id": video_id,
                        "channel": info.get("channel"),
                        "duration_seconds": info.get("duration"),
                        "transcript": transcript_text,
                        "ingredients": parsed["ingredients"],
                        "steps": parsed["steps"],
                        "description": info.get("description", ""),
                        "transcript_source": transcript_source,
                    },
                    metadata={
                        "url": url,
                        "video_id": video_id,
                        "adapter": "YouTubeRecipeAdapter",
                        "transcript_source": transcript_source,
                        "language": parsed["language"],
                    },
                )
                records.append(record)

            except Exception as exc:
                self.errors.append(
                    {
                        "url": url,
                        "source_id": self.source_id,
                        "error": str(exc),
                    }
                )

        return records

    def _extract_video_info(self, url: str) -> Dict[str, Any]:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "user_agent": self.user_agent,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not isinstance(info, dict):
            return {}

        return info

    def _get_transcript_text(
        self,
        video_id: Optional[str],
        fallback_text: str = "",
    ) -> tuple[str, str]:
        if not video_id:
            return fallback_text or "", "description_fallback"

        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=self.transcript_languages,
            )
            text = " ".join(chunk.get("text", "").strip() for chunk in transcript if chunk.get("text"))
            text = re.sub(r"\s+", " ", text).strip()
            return text or fallback_text or "", "youtube_transcript_api"
        except (TranscriptsDisabled, NoTranscriptFound):
            return fallback_text or "", "description_fallback"
        except Exception:
            return fallback_text or "", "description_fallback"

    def _parse_transcript(self, transcript: str) -> Dict[str, Any]:
        if not transcript:
            return {
                "ingredients": [],
                "steps": [],
                "language": "unknown",
            }

        lines = self._split_transcript_into_lines(transcript)
        ingredients: List[str] = []
        steps: List[str] = []

        in_ingredients = False
        in_steps = False

        for line in lines:
            lower = line.lower()

            if self._looks_like_heading(lower, ["ingredients", "ingredient list"]):
                in_ingredients = True
                in_steps = False
                continue

            if self._looks_like_heading(lower, ["instructions", "method", "steps", "directions", "procedure"]):
                in_steps = True
                in_ingredients = False
                continue

            if in_ingredients:
                if self._looks_like_ingredient_line(line):
                    ingredients.append(line)
                continue

            if in_steps:
                if line:
                    steps.append(line)
                continue

        # Fallback: if no clear sections exist, infer from transcript
        if not ingredients:
            ingredients = self._guess_ingredients_from_transcript(lines)

        if not steps:
            steps = self._guess_steps_from_transcript(lines)

        return {
            "ingredients": self._dedupe_preserve_order(ingredients),
            "steps": self._dedupe_preserve_order(steps),
            "language": "en",
        }

    def _split_transcript_into_lines(self, transcript: str) -> List[str]:
        # Convert long transcript text into manageable lines/sentences
        raw_parts = re.split(r"[\n\r]+|(?<=[.!?])\s+", transcript)
        lines: List[str] = []
        for part in raw_parts:
            cleaned = self._cleanup_transcript_text(part)
            if cleaned:
                lines.append(cleaned)
        return lines

    def _cleanup_transcript_text(self, text: str) -> str:
        value = str(text).strip()
        if not value:
            return ""

        # Remove timestamps like 00:12, 1:23:45, [00:12]
        value = re.sub(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?", "", value)
        value = re.sub(r"^\s*\d{1,2}:\d{2}(?::\d{2})?\s*", "", value)

        # Remove speaker markers
        value = re.sub(r"^\s*[A-Z][A-Z0-9 _-]{1,20}:\s*", "", value)

        value = re.sub(r"\s+", " ", value).strip(" -–—:;,.")
        return value

    def _looks_like_heading(self, text: str, phrases: List[str]) -> bool:
        t = text.strip().lower()
        return any(t == phrase or t.startswith(phrase + " ") or phrase in t for phrase in phrases)

    def _looks_like_ingredient_line(self, line: str) -> bool:
        text = line.strip().lower()
        if not text:
            return False

        unit_terms = (
            "cup", "cups", "tbsp", "tsp", "teaspoon", "tablespoon",
            "gram", "kg", "ml", "pinch", "clove", "slice", "bowl",
            "handful", "piece", "pieces", "can",
        )

        has_quantity = bool(re.search(r"\b\d+(\.\d+)?\b", text))
        has_unit = any(term in text for term in unit_terms)

        return has_quantity or has_unit or text.startswith("- ")

    def _guess_ingredients_from_transcript(self, lines: List[str]) -> List[str]:
        ingredients: List[str] = []
        for line in lines:
            if self._looks_like_ingredient_line(line):
                ingredients.append(line)
        return ingredients

    def _guess_steps_from_transcript(self, lines: List[str]) -> List[str]:
        steps: List[str] = []
        for line in lines:
            if line and not self._looks_like_ingredient_line(line):
                steps.append(line)
        return steps[:30]

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items:
            cleaned = self._cleanup_transcript_text(item)
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
        return out

    def _video_id_from_url(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        if "youtu.be" in parsed.netloc:
            return parsed.path.strip("/") or None

        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]

        match = re.search(r"(?:v=|/shorts/|/embed/)([A-Za-z0-9_-]{6,20})", url)
        if match:
            return match.group(1)

        return None

    def _title_from_url(self, url: str) -> Optional[str]:
        video_id = self._video_id_from_url(url)
        if not video_id:
            return None
        return f"YouTube Video {video_id}"

    def _first_non_empty(self, *values: Any) -> Optional[str]:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None