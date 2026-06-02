from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .raw_record import RawRecord


class SourceAdapter(ABC):
    def __init__(self, source_id: str, source_type: str, version: str = "1.0") -> None:
        self.source_id = source_id
        self.source_type = source_type
        self.version = version

    def validate_config(self) -> None:
        return None

    @abstractmethod
    def extract(self) -> List[RawRecord]:
        raise NotImplementedError