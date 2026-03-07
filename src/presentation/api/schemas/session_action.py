from __future__ import annotations

import re
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.session.actions import SessionAction

VERB_NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class SessionActionSchema(BaseModel):
    """Session actions 的共享表示。"""

    verb: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="动作类型，必须采用 domain.verb 命名空间格式。",
        examples=["social.posted"],
    )
    description: str | None = Field(
        default=None,
        max_length=256,
        description="动作说明。",
    )
    details_schema: dict[str, Any] = Field(
        ...,
        description="动作 details 的 JSON Schema（当前要求 type=object）。",
    )

    @field_validator("verb")
    @classmethod
    def _validate_verb_namespace(cls, value: str) -> str:
        """校验 verb 必须满足 domain.verb 命名空间格式。"""
        if VERB_NAMESPACE_PATTERN.match(value) is None:
            raise ValueError("verb 格式非法，必须为 domain.verb。")
        return value

    @field_validator("details_schema")
    @classmethod
    def _validate_details_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        """校验 details_schema 至少是 object schema。"""
        if value.get("type") != "object":
            raise ValueError("details_schema.type 必须为 object。")
        try:
            Draft202012Validator.check_schema(value)
        except SchemaError as exc:
            raise ValueError(f"details_schema 非法: {exc.message}") from exc
        return value

    def to_domain(self) -> SessionAction:
        """转为领域对象。"""
        return SessionAction(
            verb=self.verb,
            description=self.description,
            details_schema=dict(self.details_schema),
        )

    @classmethod
    def from_domain(cls, action: SessionAction) -> SessionActionSchema:
        """由领域对象构造响应模型。"""
        return cls(
            verb=action.verb,
            description=action.description,
            details_schema=dict(action.details_schema),
        )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
