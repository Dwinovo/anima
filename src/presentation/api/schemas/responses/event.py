from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EventReportData(BaseModel):
    """Event 上报成功后的响应体。"""

    session_id: str
    event_id: str
    world_time: int
    verb: str
    accepted: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = ["EventReportData"]
