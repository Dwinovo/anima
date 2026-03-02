from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateData(BaseModel):
    """
    Response payload for session creation.
    """

    session_id: str = Field(
        ...,
        description="Unique identifier of the created session.",
        examples=["session_ab12cd34"],
    )

    name: str = Field(
        ...,
        description="Session display name.",
        examples=["Cyber City Alpha"],
    )

    description: str | None = Field(
        default=None,
        description="Optional session description.",
    )

    max_agents_limit: int = Field(
        ...,
        description="Maximum allowed agents in this session.",
        examples=[1000],
    )

    default_llm: str | None = Field(
        default=None,
        description="Default LLM model configured for this session.",
        examples=["gpt-4o"],
    )

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,  # 响应模型不可变（更安全）
    )


class SessionDetailData(BaseModel):
    """
    Response payload for retrieving a session detail.
    """

    session_id: str
    name: str
    description: str | None
    max_agents_limit: int
    default_llm: str | None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SessionListItem(BaseModel):
    """
    Lightweight item for listing sessions.
    """

    session_id: str
    name: str
    max_agents_limit: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SessionListData(BaseModel):
    """
    Response payload for session list endpoint.
    """

    items: list[SessionListItem]
    total: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = [
    "SessionCreateData",
    "SessionDetailData",
    "SessionListItem",
    "SessionListData",
]
