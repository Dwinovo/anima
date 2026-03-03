from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AgentRegisterRequest(BaseModel):
    """注册 Agent 请求体。"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Agent 昵称，后端会据此生成 display_name。",
        examples=["Alice"],
    )
    profile: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Agent 简短名片描述。",
        examples=["我是一个谨慎的观察者。"],
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        """校验昵称非空。"""
        if not value:
            raise ValueError("name 不能为空。")
        return value

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: str) -> str:
        """校验名片非空。"""
        if not value:
            raise ValueError("profile 不能为空。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class AgentPatchRequest(BaseModel):
    """编辑 Agent 请求体。"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="新的 Agent 昵称，若更新则后端会重算 display_name。",
        examples=["AliceNew"],
    )
    profile: str | None = Field(
        default=None,
        min_length=1,
        max_length=2048,
        description="新的 Agent 名片描述。",
        examples=["我是一个更关注效率的观察者。"],
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

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: str | None) -> str | None:
        """校验名片非空。"""
        if value is None:
            return None
        if not value:
            raise ValueError("profile 不能为空。")
        return value

    @model_validator(mode="after")
    def _validate_non_empty_patch(self) -> AgentPatchRequest:
        """校验 PATCH 请求至少包含一个可更新字段。"""
        if self.name is None and self.profile is None:
            raise ValueError("至少需要提供一个可更新字段：name 或 profile。")
        return self

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class AgentTokenRefreshRequest(BaseModel):
    """刷新 Agent Token 请求体。"""

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


__all__ = ["AgentPatchRequest", "AgentRegisterRequest", "AgentTokenRefreshRequest"]
