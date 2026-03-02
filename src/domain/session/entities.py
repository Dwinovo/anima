from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Session:
    session_id: str
    name: str
    description: str | None
    max_agents_limit: int
    default_llm: str | None
    created_at: datetime
    updated_at: datetime | None
