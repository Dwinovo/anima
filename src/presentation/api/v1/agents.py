from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.application.usecases.agent.register_agent import RegisterAgentUseCase
from src.application.usecases.agent.unregister_agent import UnregisterAgentUseCase
from src.presentation.api.constants.http_status import AGENT_REGISTERED, AGENT_REMOVED
from src.presentation.api.dependencies import (
    get_register_agent_usecase,
    get_unregister_agent_usecase,
)
from src.presentation.api.schemas.requests.agent import AgentRegisterRequest
from src.presentation.api.schemas.responses.agent import AgentRegisterData
from src.presentation.api.schemas.responses.envelope import ApiResponse

router = APIRouter(prefix="/sessions/{session_id}/agents", tags=["agents"])


@router.post(
    "/{uuid}",
    status_code=AGENT_REGISTERED,
    response_model=ApiResponse[AgentRegisterData],
    summary="Register agent",
)
async def register_agent(
    session_id: str,
    uuid: str,
    payload: AgentRegisterRequest,
    usecase: RegisterAgentUseCase = Depends(get_register_agent_usecase),
) -> ApiResponse[AgentRegisterData]:
    """注册 Agent 并写入在线状态与画像缓存。"""
    result = await usecase.execute(
        session_id=session_id,
        uuid=uuid,
        name=payload.name,
        profile=payload.profile,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=AgentRegisterData(
            session_id=result.session_id,
            uuid=result.uuid,
            name=result.name or payload.name,
            display_name=result.display_name or payload.name,
            active=result.active,
        ),
    )


@router.delete(
    "/{uuid}",
    status_code=AGENT_REMOVED,
    summary="Unregister agent",
    response_class=Response,
)
async def unregister_agent(
    session_id: str,
    uuid: str,
    usecase: UnregisterAgentUseCase = Depends(get_unregister_agent_usecase),
) -> Response:
    """卸载 Agent 并清理在线状态与画像缓存。"""
    await usecase.execute(session_id=session_id, uuid=uuid)
    return Response(status_code=AGENT_REMOVED)
