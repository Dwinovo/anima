from __future__ import annotations

import asyncio
from contextlib import suppress
from time import time

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from fastapi.websockets import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from src.application.usecases.agent.get_agent import GetAgentUseCase
from src.application.usecases.agent.get_agent_context import GetAgentContextUseCase
from src.application.usecases.agent.maintain_presence import MaintainAgentPresenceUseCase
from src.application.usecases.agent.patch_agent import PatchAgentUseCase
from src.application.usecases.agent.refresh_agent_tokens import RefreshAgentTokensUseCase
from src.application.usecases.agent.register_agent import RegisterAgentUseCase
from src.application.usecases.agent.unregister_agent import UnregisterAgentUseCase
from src.core.exceptions import AnimaException
from src.domain.agent.auth_state_repository import AgentAuthStateRepository
from src.domain.agent.token_service import AgentTokenService, TokenClaims
from src.presentation.api.constants.http_status import AGENT_REGISTERED, AGENT_REMOVED, HTTP_200_OK
from src.presentation.api.dependencies import (
    get_agent_context_usecase,
    get_auth_state_repo,
    get_get_agent_usecase,
    get_maintain_agent_presence_usecase,
    get_patch_agent_usecase,
    get_refresh_agent_tokens_usecase,
    get_register_agent_usecase,
    get_token_service,
    get_unregister_agent_usecase,
    require_agent_access_claims,
    validate_agent_access_token,
)
from src.presentation.api.schemas.requests.agent import (
    AgentPatchRequest,
    AgentRegisterRequest,
    AgentTokenRefreshRequest,
)
from src.presentation.api.schemas.responses.agent import (
    AgentContextData,
    AgentContextEventItem,
    AgentContextMediaEvents,
    AgentDetailData,
    AgentRegisterData,
    AgentTokenRefreshData,
)
from src.presentation.api.schemas.responses.envelope import ApiResponse

router = APIRouter(prefix="/sessions/{session_id}/agents", tags=["agents"])
HEARTBEAT_INTERVAL_SECONDS = 60
MAX_MISSED_HEARTBEATS = 3
HEARTBEAT_TTL_SECONDS = HEARTBEAT_INTERVAL_SECONDS * MAX_MISSED_HEARTBEATS


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
            token_type=result.token_type or "Bearer",
            access_token=result.access_token or "",
            access_token_expires_in=result.access_token_expires_in or 0,
            refresh_token=result.refresh_token or "",
            refresh_token_expires_in=result.refresh_token_expires_in or 0,
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
    _: TokenClaims = Depends(require_agent_access_claims),
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
    _: TokenClaims = Depends(require_agent_access_claims),
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
    _: TokenClaims = Depends(require_agent_access_claims),
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
    media_public_events = [
        AgentContextEventItem(
            event_id=item.event_id,
            world_time=item.world_time,
            verb=item.verb,
            subject_uuid=item.subject_uuid,
            target_ref=item.target_ref,
            details=item.details,
        )
        for item in result.media_public_events
    ]
    media_following_events = [
        AgentContextEventItem(
            event_id=item.event_id,
            world_time=item.world_time,
            verb=item.verb,
            subject_uuid=item.subject_uuid,
            target_ref=item.target_ref,
            details=item.details,
        )
        for item in result.media_following_events
    ]
    self_events = [
        AgentContextEventItem(
            event_id=item.event_id,
            world_time=item.world_time,
            verb=item.verb,
            subject_uuid=item.subject_uuid,
            target_ref=item.target_ref,
            details=item.details,
        )
        for item in result.self_events
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=AgentContextData(
            session_id=result.session_id,
            agent_id=result.agent_id,
            current_world_time=result.current_world_time,
            status_events=status_events,
            media_events=AgentContextMediaEvents(
                public_feed=media_public_events,
                following_feed=media_following_events,
            ),
            self_events=self_events,
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
    _: TokenClaims = Depends(require_agent_access_claims),
    usecase: UnregisterAgentUseCase = Depends(get_unregister_agent_usecase),
) -> Response:
    """卸载 Agent 并清理在线状态与运行态缓存。"""
    await usecase.execute(session_id=session_id, agent_id=agent_id)
    return Response(status_code=AGENT_REMOVED)


@router.post(
    "/{agent_id}/tokens/refresh",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[AgentTokenRefreshData],
    summary="Refresh agent tokens",
)
async def refresh_agent_tokens(
    session_id: str,
    agent_id: str,
    payload: AgentTokenRefreshRequest,
    usecase: RefreshAgentTokensUseCase = Depends(get_refresh_agent_tokens_usecase),
) -> ApiResponse[AgentTokenRefreshData]:
    """刷新 Agent access token 并轮换 refresh token。"""
    result = await usecase.execute(
        session_id=session_id,
        agent_id=agent_id,
        refresh_token=payload.refresh_token,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=AgentTokenRefreshData(
            token_type=result.token_type or "Bearer",
            access_token=result.access_token or "",
            access_token_expires_in=result.access_token_expires_in or 0,
            refresh_token=result.refresh_token or "",
            refresh_token_expires_in=result.refresh_token_expires_in or 0,
        ),
    )


@router.websocket("/{agent_id}/presence")
async def agent_presence(
    websocket: WebSocket,
    session_id: str,
    agent_id: str,
    access_token: str | None = Query(default=None),
    usecase: MaintainAgentPresenceUseCase = Depends(get_maintain_agent_presence_usecase),
    token_service: AgentTokenService = Depends(get_token_service),
    auth_state_repo: AgentAuthStateRepository = Depends(get_auth_state_repo),
) -> None:
    """维护 Agent Presence 长连接心跳。"""
    await websocket.accept()
    if access_token is None:
        await websocket.send_json(
            {
                "type": "error",
                "code": 40101,
                "message": "Missing access token.",
            }
        )
        await websocket.close(code=1008)
        return
    try:
        await validate_agent_access_token(
            token=access_token,
            session_id=session_id,
            agent_id=agent_id,
            token_service=token_service,
            auth_state_repo=auth_state_repo,
        )
    except AnimaException as exc:
        await websocket.send_json(
            {
                "type": "error",
                "code": exc.code,
                "message": exc.message,
            }
        )
        await websocket.close(code=1008)
        return
    try:
        await usecase.on_connect(
            session_id=session_id,
            agent_id=agent_id,
            heartbeat_ttl_seconds=HEARTBEAT_TTL_SECONDS,
        )
    except AnimaException as exc:
        with suppress(RuntimeError):
            await websocket.send_json(
                {
                    "type": "error",
                    "code": exc.code,
                    "message": exc.message,
                }
            )
            await websocket.close(code=1008)
        return

    await websocket.send_json(
        {
            "type": "hello",
            "session_id": session_id,
            "agent_id": agent_id,
            "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
            "max_missed_heartbeats": MAX_MISSED_HEARTBEATS,
        }
    )

    missed_heartbeats = 0
    try:
        while True:
            await websocket.send_json({"type": "ping", "ts": int(time())})
            try:
                payload = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=HEARTBEAT_INTERVAL_SECONDS,
                )
            except asyncio.TimeoutError:
                missed_heartbeats += 1
                if missed_heartbeats >= MAX_MISSED_HEARTBEATS:
                    break
                continue
            except WebSocketDisconnect:
                break

            if not isinstance(payload, dict):
                continue

            message_type = payload.get("type")
            if message_type not in {"pong", "ping"}:
                continue

            missed_heartbeats = 0
            await usecase.on_pong(
                session_id=session_id,
                agent_id=agent_id,
                heartbeat_ttl_seconds=HEARTBEAT_TTL_SECONDS,
            )
            if message_type == "ping":
                await websocket.send_json({"type": "pong", "ts": int(time())})
    finally:
        await usecase.on_disconnect(session_id=session_id, agent_id=agent_id)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            with suppress(RuntimeError):
                await websocket.close(code=1000)
