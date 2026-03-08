from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.presentation.api.schemas.session_action import SessionActionSchema


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
        description="Session 展示名，由管理面板传入。",
        examples=["Demo Social Session"],
    )

    description: str | None = Field(
        default=None,
        max_length=1024,
        description="Optional description of the session.",
        examples=["A social experiment session."],
    )

    max_entities_limit: int = Field(
        ...,
        ge=1,
        le=100_000,
        description="Maximum number of entities allowed in this session.",
        examples=[1000],
    )
    actions: list[SessionActionSchema] = Field(
        ...,
        description="Session 级动作注册表，创建时必须显式提交，可为空数组。",
    )

    @field_validator("actions")
    @classmethod
    def _validate_unique_action_verbs(
        cls,
        value: list[SessionActionSchema],
    ) -> list[SessionActionSchema]:
        """校验 actions 中 verb 唯一。"""
        verbs = [item.verb for item in value]
        if len(set(verbs)) != len(verbs):
            raise ValueError("actions 中存在重复 verb。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )


class SessionPatchRequest(BaseModel):
    """Session PATCH 请求体。"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Session 展示名。",
    )
    description: str | None = Field(
        default=None,
        max_length=1024,
        description="Session 描述。",
    )
    max_entities_limit: int | None = Field(
        default=None,
        ge=1,
        le=100_000,
        description="最大 Entity 上限。",
    )
    actions: list[SessionActionSchema] | None = Field(
        default=None,
        description="可选更新 Session 级动作注册表（可为空数组）；提交后立即生效。",
    )

    @field_validator("actions")
    @classmethod
    def _validate_patch_unique_action_verbs(
        cls,
        value: list[SessionActionSchema] | None,
    ) -> list[SessionActionSchema] | None:
        """校验 PATCH 的 actions 中 verb 唯一。"""
        if value is None:
            return None
        verbs = [item.verb for item in value]
        if len(set(verbs)) != len(verbs):
            raise ValueError("actions 中存在重复 verb。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


__all__ = [
    "SessionCreateRequest",
    "SessionPatchRequest",
]
