from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.application.usecases.agent.get_agent import GetAgentUseCase
from src.application.usecases.agent.get_agent_context import GetAgentContextUseCase
from src.application.usecases.agent.patch_agent import PatchAgentUseCase
from src.application.usecases.agent.register_agent import RegisterAgentUseCase
from src.application.usecases.agent.unregister_agent import UnregisterAgentUseCase
from src.presentation.api.constants.http_status import AGENT_REGISTERED, AGENT_REMOVED, HTTP_200_OK
from src.presentation.api.dependencies import (
    get_agent_context_usecase,
    get_get_agent_usecase,
    get_patch_agent_usecase,
    get_register_agent_usecase,
    get_unregister_agent_usecase,
)
from src.presentation.api.schemas.requests.agent import AgentPatchRequest, AgentRegisterRequest
from src.presentation.api.schemas.responses.agent import (
    AgentContextData,
    AgentContextEventItem,
    AgentDetailData,
    AgentRegisterData,
)
from src.presentation.api.schemas.responses.envelope import ApiResponse

router = APIRouter(prefix="/sessions/{session_id}/agents", tags=["agents"])


@router.post(
    "",
    status_code=AGENT_REGISTERED,
    response_model=ApiResponse[AgentRegisterData],
    summary="Register agent",
)
async def register_agent(
    session_id: str,
    payload: AgentRegisterRequest,
    usecase: RegisterAgentUseCase = Depends(get_register_agent_usecase),
) -> ApiResponse[AgentRegisterData]:
    """注册 Agent 并写入在线状态与运行态缓存。"""
    result = await usecase.execute(
        session_id=session_id,
        name=payload.name,
        profile=payload.profile,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=AgentRegisterData(
            session_id=result.session_id,
            agent_id=result.agent_id,
            name=result.name or payload.name,
            display_name=result.display_name or payload.name,
        ),
    )


@router.get(
    "/{agent_id}",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[AgentDetailData],
    summary="Get agent",
)
async def get_agent(
    session_id: str,
    agent_id: str,
    usecase: GetAgentUseCase = Depends(get_get_agent_usecase),
) -> ApiResponse[AgentDetailData]:
    """读取 Agent 当前信息。"""
    result = await usecase.execute(session_id=session_id, agent_id=agent_id)
    return ApiResponse(
        code=0,
        message="success",
        data=AgentDetailData(
            session_id=result.session_id,
            agent_id=result.agent_id,
            name=result.name or "",
            display_name=result.display_name or "",
            profile=result.profile,
            active=result.active,
        ),
    )


@router.patch(
    "/{agent_id}",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[AgentDetailData],
    summary="Patch agent",
)
async def patch_agent(
    session_id: str,
    agent_id: str,
    payload: AgentPatchRequest,
    usecase: PatchAgentUseCase = Depends(get_patch_agent_usecase),
) -> ApiResponse[AgentDetailData]:
    """更新 Agent 昵称并重算展示名。"""
    result = await usecase.execute(
        session_id=session_id,
        agent_id=agent_id,
        name=payload.name,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=AgentDetailData(
            session_id=result.session_id,
            agent_id=result.agent_id,
            name=result.name or payload.name,
            display_name=result.display_name or payload.name,
            profile=result.profile,
            active=result.active,
        ),
    )


@router.get(
    "/{agent_id}/context",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[AgentContextData],
    summary="Get agent context",
)
async def get_agent_context(
    session_id: str,
    agent_id: str,
    usecase: GetAgentContextUseCase = Depends(get_agent_context_usecase),
) -> ApiResponse[AgentContextData]:
    """获取 Agent 在社交平台中的上下文事件。"""
    result = await usecase.execute(session_id=session_id, agent_id=agent_id)
    status_events = [
        AgentContextEventItem(
            event_id=item.event_id,
            world_time=item.world_time,
            verb=item.verb,
            subject_uuid=item.subject_uuid,
            target_ref=item.target_ref,
            details=item.details,
        )
        for item in result.status_events
    ]
    media_events = [
        AgentContextEventItem(
            event_id=item.event_id,
            world_time=item.world_time,
            verb=item.verb,
            subject_uuid=item.subject_uuid,
            target_ref=item.target_ref,
            details=item.details,
        )
        for item in result.media_events
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=AgentContextData(
            session_id=result.session_id,
            agent_id=result.agent_id,
            status_events=status_events,
            media_events=media_events,
        ),
    )


@router.delete(
    "/{agent_id}",
    status_code=AGENT_REMOVED,
    summary="Unregister agent",
    response_class=Response,
)
async def unregister_agent(
    session_id: str,
    agent_id: str,
    usecase: UnregisterAgentUseCase = Depends(get_unregister_agent_usecase),
) -> Response:
    """卸载 Agent 并清理在线状态与运行态缓存。"""
    await usecase.execute(session_id=session_id, agent_id=agent_id)
    return Response(status_code=AGENT_REMOVED)
