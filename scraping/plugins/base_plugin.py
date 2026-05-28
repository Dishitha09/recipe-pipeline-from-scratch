from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RecipeSourcePlugin(ABC):
    @abstractmethod
    def scrape(self, urls: List[str]) -> List[Dict[str, Any]]:
        pass