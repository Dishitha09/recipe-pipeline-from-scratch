from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
import uuid


@dataclass(frozen=True)
class RawRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    source_id: str = ""
    source_type: str = ""

    version: str = "1.0"

    ingested_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    raw_content: Dict[str, Any] = field(default_factory=dict)