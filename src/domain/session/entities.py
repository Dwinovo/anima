from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Session:
    """Session 领域实体。"""

    session_id: str
    name: str
    description: str | None
    max_entities_limit: int
    created_at: datetime
    updated_at: datetime
