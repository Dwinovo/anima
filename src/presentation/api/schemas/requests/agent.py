from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentRegisterRequest(BaseModel):
    """
    HTTP request schema for registering an agent.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Agent 在设计平台中的昵称。",
        examples=["Alice"],
    )
    profile: dict[str, Any] = Field(
        ...,
        description="Agent profile payload used by cognition pipeline.",
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

__all__ = ["AgentRegisterRequest"]
