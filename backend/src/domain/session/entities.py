from dataclasses import dataclass, field
from datetime import datetime

from src.domain.session.actions import SessionAction


@dataclass(slots=True)
class Session:
    """Session 领域实体。"""

    session_id: str
    name: str
    description: str | None
    max_entities_limit: int
    created_at: datetime
    updated_at: datetime
    actions: tuple[SessionAction, ...] = field(default_factory=tuple)
