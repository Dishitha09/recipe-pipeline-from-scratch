from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from .audio_adapter import AudioRecipeAdapter
from .image_adapter import ImageRecipeAdapter
from .pdf_adapter import PDFRecipeAdapter
from .source_adapter import SourceAdapter
from .text_adapter import TextRecipeAdapter
from .web_adapter import WebScraperAdapter
from .youtube_adapter import YouTubeRecipeAdapter


ADAPTER_MAP = {
    "WebScraperAdapter": WebScraperAdapter,
    "YouTubeRecipeAdapter": YouTubeRecipeAdapter,
    "AudioRecipeAdapter": AudioRecipeAdapter,
    "PDFRecipeAdapter": PDFRecipeAdapter,
    "TextRecipeAdapter": TextRecipeAdapter,
    "ImageRecipeAdapter": ImageRecipeAdapter,
}


class SourceRegistry:
    def __init__(self, registry_path: str | Path) -> None:
        self.registry_path = Path(registry_path)
        self._mtime: float | None = None
        self._data: Dict[str, object] = {}

    def load(self) -> Dict[str, object]:
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry file not found: {self.registry_path}")

        with open(self.registry_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

        self._mtime = self.registry_path.stat().st_mtime
        return self._data

    def refresh_if_needed(self) -> Dict[str, object]:
        current_mtime = self.registry_path.stat().st_mtime if self.registry_path.exists() else None
        if self._mtime is None or current_mtime != self._mtime:
            return self.load()
        return self._data

    def load_adapters(self) -> List[SourceAdapter]:
        data = self.refresh_if_needed()
        adapter_defs = data.get("adapters", {}) if isinstance(data, dict) else {}

        adapters: List[SourceAdapter] = []
        for source_key, spec in adapter_defs.items():
            if not isinstance(spec, dict):
                raise ValueError(f"Invalid registry entry for {source_key}")

            adapter_name = spec.get("adapter")
            adapter_cls = ADAPTER_MAP.get(adapter_name)
            if adapter_cls is None:
                raise ValueError(f"Unknown adapter class: {adapter_name}")

            config = spec.get("config", {}) or {}
            source_id = spec.get("source_id", source_key)
            source_type = spec.get("source_type", "web")
            version = str(spec.get("version", "1.0"))

            adapter = adapter_cls(
                source_id=source_id,
                source_type=source_type,
                version=version,
                **config,
            )
            adapter.validate_config()
            adapters.append(adapter)

        return adapters