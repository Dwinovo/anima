from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EntityRegisterRequest(BaseModel):
    """注册 Entity 请求体。"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Entity 昵称，后端会据此生成 display_name。",
        examples=["Alice"],
    )
    source: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Entity 来源标识，仅用于标注实体来自哪个客户端/世界。",
        examples=["minecraft"],
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        """校验昵称非空。"""
        if not value:
            raise ValueError("name 不能为空。")
        return value

    @field_validator("source")
    @classmethod
    def _validate_source(cls, value: str) -> str:
        """校验来源标识非空。"""
        if not value:
            raise ValueError("source 不能为空。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class EntityPatchRequest(BaseModel):
    """编辑 Entity 请求体。"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="新的 Entity 昵称，若更新则后端会重算 display_name。",
        examples=["AliceNew"],
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str | None) -> str | None:
        """校验昵称非空。"""
        if value is None:
            return None
        if not value:
            raise ValueError("name 不能为空。")
        return value

    @model_validator(mode="after")
    def _validate_non_empty_patch(self) -> EntityPatchRequest:
        """校验 PATCH 请求至少包含一个可更新字段。"""
        if self.name is None:
            raise ValueError("至少需要提供一个可更新字段：name。")
        return self

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class EntityTokenRefreshRequest(BaseModel):
    """刷新 Entity Token 请求体。"""

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="用于刷新 access token 的 refresh token。",
        examples=["<REFRESH_TOKEN>"],
    )

    @field_validator("refresh_token")
    @classmethod
    def _validate_refresh_token(cls, value: str) -> str:
        """校验 refresh token 非空。"""
        if not value:
            raise ValueError("refresh_token 不能为空。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


__all__ = ["EntityPatchRequest", "EntityRegisterRequest", "EntityTokenRefreshRequest"]
