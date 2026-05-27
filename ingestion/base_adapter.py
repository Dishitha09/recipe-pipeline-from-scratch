from abc import ABC, abstractmethod
from typing import List

from ingestion.raw_record import RawRecord


class SourceAdapter(ABC):

    @abstractmethod
    def extract(self) -> List[RawRecord]:
        pass

    @abstractmethod
    def validate_config(self):
        pass