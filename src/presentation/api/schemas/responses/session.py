from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateData(BaseModel):
    """
    Response payload for session creation.
    """

    session_id: str = Field(
        ...,
        description="Unique identifier of the created session.",
        examples=["c4f2ab16-93a6-4e69-a0aa-1f96f4548b6c"],
    )

    name: str = Field(
        ...,
        description="Session display name.",
        examples=["Demo Social Session"],
    )

    description: str | None = Field(
        default=None,
        description="Optional session description.",
    )

    max_entities_limit: int = Field(
        ...,
        description="Maximum allowed entities in this session.",
        examples=[1000],
    )

    created_at: datetime
    updated_at: datetime

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
    max_entities_limit: int
    created_at: datetime
    updated_at: datetime

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
    description: str | None
    max_entities_limit: int

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
