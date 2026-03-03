from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateRequest(BaseModel):
    """
    HTTP request schema for creating a new session.

    This schema belongs to Presentation layer.
    It must not be imported into Domain layer.
    """

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Session 唯一标识，由管理面板传入。",
        examples=["session_demo_001"],
    )

    description: str | None = Field(
        default=None,
        max_length=1024,
        description="Optional description of the session.",
        examples=["A social experiment session."],
    )

    max_agents_limit: int = Field(
        ...,
        ge=1,
        le=100_000,
        description="Maximum number of agents allowed in this session.",
        examples=[1000],
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )


class SessionPatchRequest(BaseModel):
    """Session PATCH 请求体。"""

    description: str | None = Field(
        default=None,
        max_length=1024,
        description="Session 描述。",
    )
    max_agents_limit: int | None = Field(
        default=None,
        ge=1,
        le=100_000,
        description="最大 Agent 上限。",
    )
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


__all__ = [
    "SessionCreateRequest",
    "SessionPatchRequest",
]
