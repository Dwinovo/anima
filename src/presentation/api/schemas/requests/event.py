from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventSubjectRequest(BaseModel):
    """事件主语实体请求体。"""

    uuid: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="事件发起方实体唯一标识。",
        examples=["agent_a"],
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class EventActionRequest(BaseModel):
    """事件动作请求体。"""

    verb: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="动作类型，如 POSTED/REPLIED/ATTACKED。",
        examples=["POSTED"],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="动作细节载荷，会落 Mongo payload。",
    )
    is_social: bool = Field(
        default=True,
        description="是否属于社交类事件。",
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class EventTargetRequest(BaseModel):
    """事件宾语请求体。"""

    ref: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="目标引用（Agent UUID / Event ID / board:{session_id}）。",
        examples=["agent_b"],
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class EventReportRequest(BaseModel):
    """Event 上报请求体。"""

    world_time: int = Field(
        ...,
        ge=0,
        description="世界内时间戳。",
        examples=[12005],
    )
    subject: EventSubjectRequest
    action: EventActionRequest
    target: EventTargetRequest
    embedding_256: list[float] | None = Field(
        default=None,
        description="事件语义向量（可选，长度必须为 256）。",
    )
    schema_version: int = Field(
        default=1,
        ge=1,
        description="事件载荷结构版本。",
    )

    @field_validator("embedding_256")
    @classmethod
    def _validate_embedding_256(cls, value: list[float] | None) -> list[float] | None:
        """校验向量维度，确保符合规范要求。"""
        if value is None:
            return None
        if len(value) != 256:
            raise ValueError("embedding_256 must contain exactly 256 float values.")
        return value

    model_config = ConfigDict(
        extra="forbid",
    )


__all__ = [
    "EventSubjectRequest",
    "EventActionRequest",
    "EventTargetRequest",
    "EventReportRequest",
]
