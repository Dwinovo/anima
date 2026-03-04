from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventReportRequest(BaseModel):
    """Event 上报请求体（当前阶段弱约束）。"""

    world_time: int = Field(
        ...,
        ge=0,
        description="世界内时间戳。",
        examples=[12005],
    )
    subject_uuid: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="事件主语 Agent 标识。",
        examples=["agent_a"],
    )
    verb: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="动作类型。",
        examples=["POSTED"],
    )
    target_ref: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="目标引用（如 agent_x 或 board:session_x）。",
        examples=["board:session_demo"],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="动作细节载荷。",
    )
    schema_version: int = Field(
        default=1,
        ge=1,
        description="事件载荷结构版本。",
    )

    @field_validator("subject_uuid", "verb", "target_ref")
    @classmethod
    def _validate_required_string(cls, value: str) -> str:
        """校验关键字符串字段非空。"""
        if not value:
            raise ValueError("关键字符串字段不能为空。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


CURSOR_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]+$")


class EventListQuery(BaseModel):
    """Event 列表查询参数。"""

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="单次返回事件条数上限。",
        examples=[20],
    )
    cursor: str | None = Field(
        default=None,
        description="分页游标，格式：world_time:event_id。",
        examples=["12004:event_abc123"],
    )

    @field_validator("cursor")
    @classmethod
    def _validate_cursor(cls, value: str | None) -> str | None:
        """校验游标格式是否合法。"""
        if value is None:
            return None
        if CURSOR_PATTERN.match(value) is None:
            raise ValueError("cursor 格式非法，必须为 world_time:event_id。")
        return value

    def parse_cursor(self) -> tuple[int | None, str | None]:
        """将游标解析为 world_time 与 event_id。"""
        if self.cursor is None:
            return None, None
        world_time_raw, event_id = self.cursor.split(":", maxsplit=1)
        return int(world_time_raw), event_id

    model_config = ConfigDict(
        extra="forbid",
    )


__all__ = ["EventListQuery", "EventReportRequest"]
