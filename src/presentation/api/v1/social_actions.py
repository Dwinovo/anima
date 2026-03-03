from __future__ import annotations

from fastapi import APIRouter

from src.infrastructure.llm.tool_calling.social_actions import list_social_action_specs
from src.presentation.api.constants.http_status import HTTP_200_OK
from src.presentation.api.schemas.responses.envelope import ApiResponse
from src.presentation.api.schemas.responses.social_action import (
    SocialActionItemData,
    SocialActionListData,
)

router = APIRouter(prefix="/social-actions", tags=["social-actions"])


@router.get(
    "",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[SocialActionListData],
    summary="List social actions",
)
async def list_social_actions() -> ApiResponse[SocialActionListData]:
    """列出服务端支持的社交动作协议元信息。"""
    specs = list_social_action_specs()
    items = [
        SocialActionItemData(
            tool_name=item["tool_name"],
            verb=item["verb"],
            description=item["description"],
            allowed_target_topologies=item["allowed_target_topologies"],
            parameters_schema=item["parameters_schema"],
        )
        for item in specs
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=SocialActionListData(
            items=items,
            total=len(items),
        ),
    )
