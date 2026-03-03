from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="新的 Agent 昵称，后端会重算 display_name。",
        examples=["AliceNew"],
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        """校验昵称非空。"""
        if not value:
            raise ValueError("name 不能为空。")
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


__all__ = ["AgentPatchRequest", "AgentRegisterRequest"]
