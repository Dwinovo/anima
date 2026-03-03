from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SocialActionItemData(BaseModel):
    """社交动作元信息单项。"""

    tool_name: str = Field(..., description="Tool calling 名称。")
    verb: str = Field(..., description="标准动作枚举值。")
    description: str = Field(..., description="动作说明。")
    allowed_target_topologies: list[str] = Field(
        ...,
        description="允许的目标拓扑类型。",
    )
    parameters_schema: dict[str, Any] = Field(
        ...,
        description="动作参数 JSON Schema。",
    )

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SocialActionListData(BaseModel):
    """社交动作元信息列表。"""

    items: list[SocialActionItemData]
    total: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = ["SocialActionItemData", "SocialActionListData"]
