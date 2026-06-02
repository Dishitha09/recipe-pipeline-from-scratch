from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class RawRecord:
    source_id: str
    source_type: str
    version: str
    raw_content: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: str(uuid4()))
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_content", MappingProxyType(dict(self.raw_content)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "version": self.version,
            "ingested_at": self.ingested_at,
            "raw_content": dict(self.raw_content),
            "metadata": dict(self.metadata),
        }