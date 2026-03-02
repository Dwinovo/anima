from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateRequest(BaseModel):
    """
    HTTP request schema for creating a new session.

    This schema belongs to Presentation layer.
    It must not be imported into Domain layer.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Human-readable name of the session.",
        examples=["Cyber City Alpha"],
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

    default_llm: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Optional default LLM model for this session.",
        examples=["gpt-4o"],
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )


class SessionDeleteRequest(BaseModel):
    """
    Optional request body for deleting a session.

    In many REST designs, DELETE uses only path parameter.
    This schema is provided for future extension (e.g., force delete flag).
    """

    force: bool = Field(
        default=False,
        description="Force deletion including graph and payload cleanup.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class SessionListQuery(BaseModel):
    """
    Query parameters for listing sessions (future-ready design).
    """

    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of sessions to return.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )


__all__ = ["SessionCreateRequest", "SessionDeleteRequest", "SessionListQuery"]
