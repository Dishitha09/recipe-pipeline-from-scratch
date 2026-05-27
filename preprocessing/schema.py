from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PreProcessedRecipe:
    title: Optional[str] = None
    cuisine: Optional[str] = None
    prep_time: Optional[int] = None
    servings: Optional[int] = None
    ingredients: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)