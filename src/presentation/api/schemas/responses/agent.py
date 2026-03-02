from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AgentRegisterData(BaseModel):
    """
    Response payload for agent registration.
    """

    session_id: str
    uuid: str
    name: str
    display_name: str
    active: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

__all__ = ["AgentRegisterData"]
