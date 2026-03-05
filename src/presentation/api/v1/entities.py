from __future__ import annotations

import asyncio
from contextlib import suppress
from time import time

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from fastapi.websockets import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from src.application.dto.event import EventSearchItem
from src.application.usecases.entity.get_entity import GetEntityUseCase
from src.application.usecases.entity.get_entity_context import GetEntityContextUseCase
from src.application.usecases.entity.maintain_presence import MaintainEntityPresenceUseCase
from src.application.usecases.entity.patch_entity import PatchEntityUseCase
from src.application.usecases.entity.refresh_entity_tokens import RefreshEntityTokensUseCase
from src.application.usecases.entity.register_entity import RegisterEntityUseCase
from src.application.usecases.entity.unregister_entity import UnregisterEntityUseCase
from src.core.exceptions import AnimaException
from src.domain.entity.auth_state_repository import EntityAuthStateRepository
from src.domain.entity.token_service import EntityTokenService, TokenClaims
from src.presentation.api.constants.http_status import ENTITY_REGISTERED, ENTITY_REMOVED, HTTP_200_OK
from src.presentation.api.dependencies import (
    get_auth_state_repo,
    get_entity_context_usecase,
    get_get_entity_usecase,
    get_maintain_entity_presence_usecase,
    get_patch_entity_usecase,
    get_refresh_entity_tokens_usecase,
    get_register_entity_usecase,
    get_token_service,
    get_unregister_entity_usecase,
    require_entity_access_claims,
    validate_entity_access_token,
)
from src.presentation.api.schemas.requests.entity import (
    EntityPatchRequest,
    EntityRegisterRequest,
    EntityTokenRefreshRequest,
)
from src.presentation.api.schemas.responses.entity import (
    EntityContextData,
    EntityContextEventItem,
    EntityContextEventListView,
    EntityContextHotItem,
    EntityContextHotListView,
    EntityContextViews,
    EntityContextWorldSnapshot,
    EntityDetailData,
    EntityRegisterData,
    EntityTokenRefreshData,
)
from src.presentation.api.schemas.responses.envelope import ApiResponse

router = APIRouter(prefix="/sessions/{session_id}/entities", tags=["entities"])
HEARTBEAT_INTERVAL_SECONDS = 60
MAX_MISSED_HEARTBEATS = 3
HEARTBEAT_TTL_SECONDS = HEARTBEAT_INTERVAL_SECONDS * MAX_MISSED_HEARTBEATS


def _to_context_event_item(item: EventSearchItem) -> EntityContextEventItem:
    """将领域事件 DTO 映射为接口层事件项。"""
    return EntityContextEventItem(
        event_id=item.event_id,
        world_time=item.world_time,
        verb=item.verb,
        subject_uuid=item.subject_uuid,
        target_ref=item.target_ref,
        details=item.details,
    )


@router.post(
    "",
    status_code=ENTITY_REGISTERED,
    response_model=ApiResponse[EntityRegisterData],
    summary="Register entity",
)
async def register_entity(
    session_id: str,
    payload: EntityRegisterRequest,
    usecase: RegisterEntityUseCase = Depends(get_register_entity_usecase),
) -> ApiResponse[EntityRegisterData]:
    """注册 Entity 并写入在线状态与运行态缓存。"""
    result = await usecase.execute(
        session_id=session_id,
        name=payload.name,
        source=payload.source,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=EntityRegisterData(
            session_id=result.session_id,
            entity_id=result.entity_id,
            name=result.name or payload.name,
            display_name=result.display_name or payload.name,
            source=result.source or payload.source,
            token_type=result.token_type or "Bearer",
            access_token=result.access_token or "",
            access_token_expires_in=result.access_token_expires_in or 0,
            refresh_token=result.refresh_token or "",
            refresh_token_expires_in=result.refresh_token_expires_in or 0,
        ),
    )


@router.get(
    "/{entity_id}",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[EntityDetailData],
    summary="Get entity",
)
async def get_entity(
    session_id: str,
    entity_id: str,
    _: TokenClaims = Depends(require_entity_access_claims),
    usecase: GetEntityUseCase = Depends(get_get_entity_usecase),
) -> ApiResponse[EntityDetailData]:
    """读取 Entity 当前信息。"""
    result = await usecase.execute(session_id=session_id, entity_id=entity_id)
    return ApiResponse(
        code=0,
        message="success",
        data=EntityDetailData(
            session_id=result.session_id,
            entity_id=result.entity_id,
            name=result.name or "",
            display_name=result.display_name or "",
            source=result.source,
            active=result.active,
        ),
    )


@router.patch(
    "/{entity_id}",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[EntityDetailData],
    summary="Patch entity",
)
async def patch_entity(
    session_id: str,
    entity_id: str,
    payload: EntityPatchRequest,
    _: TokenClaims = Depends(require_entity_access_claims),
    usecase: PatchEntityUseCase = Depends(get_patch_entity_usecase),
) -> ApiResponse[EntityDetailData]:
    """增量更新 Entity 基础信息（name）。"""
    result = await usecase.execute(
        session_id=session_id,
        entity_id=entity_id,
        name=payload.name,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=EntityDetailData(
            session_id=result.session_id,
            entity_id=result.entity_id,
            name=result.name or "",
            display_name=result.display_name or "",
            source=result.source,
            active=result.active,
        ),
    )


@router.get(
    "/{entity_id}/context",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[EntityContextData],
    summary="Get entity context",
)
async def get_entity_context(
    session_id: str,
    entity_id: str,
    _: TokenClaims = Depends(require_entity_access_claims),
    usecase: GetEntityContextUseCase = Depends(get_entity_context_usecase),
) -> ApiResponse[EntityContextData]:
    """获取 Entity 在社交平台中的上下文事件。"""
    result = await usecase.execute(session_id=session_id, entity_id=entity_id)
    self_recent_items = [_to_context_event_item(item) for item in result.views.self_recent.items]
    public_feed_items = [_to_context_event_item(item) for item in result.views.public_feed.items]
    following_feed_items = [_to_context_event_item(item) for item in result.views.following_feed.items]
    attention_items = [_to_context_event_item(item) for item in result.views.attention.items]
    hot_items = [
        EntityContextHotItem(
            topic_ref=item.topic_ref,
            score=item.score,
            sample_event_ids=item.sample_event_ids,
        )
        for item in result.views.hot.items
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=EntityContextData(
            session_id=result.session_id,
            entity_id=result.entity_id,
            current_world_time=result.current_world_time,
            views=EntityContextViews(
                self_recent=EntityContextEventListView(
                    items=self_recent_items,
                    next_cursor=result.views.self_recent.next_cursor,
                    has_more=result.views.self_recent.has_more,
                ),
                public_feed=EntityContextEventListView(
                    items=public_feed_items,
                    next_cursor=result.views.public_feed.next_cursor,
                    has_more=result.views.public_feed.has_more,
                ),
                following_feed=EntityContextEventListView(
                    items=following_feed_items,
                    next_cursor=result.views.following_feed.next_cursor,
                    has_more=result.views.following_feed.has_more,
                ),
                attention=EntityContextEventListView(
                    items=attention_items,
                    next_cursor=result.views.attention.next_cursor,
                    has_more=result.views.attention.has_more,
                ),
                hot=EntityContextHotListView(
                    items=hot_items,
                    next_cursor=result.views.hot.next_cursor,
                    has_more=result.views.hot.has_more,
                ),
                world_snapshot=EntityContextWorldSnapshot(
                    online_entities=result.views.world_snapshot.online_entities,
                    active_entities=result.views.world_snapshot.active_entities,
                    recent_event_count=result.views.world_snapshot.recent_event_count,
                    my_following_count=result.views.world_snapshot.my_following_count,
                ),
            ),
        ),
    )


@router.delete(
    "/{entity_id}",
    status_code=ENTITY_REMOVED,
    summary="Unregister entity",
    response_class=Response,
)
async def unregister_entity(
    session_id: str,
    entity_id: str,
    _: TokenClaims = Depends(require_entity_access_claims),
    usecase: UnregisterEntityUseCase = Depends(get_unregister_entity_usecase),
) -> Response:
    """卸载 Entity 并清理在线状态与运行态缓存。"""
    await usecase.execute(session_id=session_id, entity_id=entity_id)
    return Response(status_code=ENTITY_REMOVED)


@router.post(
    "/{entity_id}/tokens/refresh",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[EntityTokenRefreshData],
    summary="Refresh entity tokens",
)
async def refresh_entity_tokens(
    session_id: str,
    entity_id: str,
    payload: EntityTokenRefreshRequest,
    usecase: RefreshEntityTokensUseCase = Depends(get_refresh_entity_tokens_usecase),
) -> ApiResponse[EntityTokenRefreshData]:
    """刷新 Entity access token 并轮换 refresh token。"""
    result = await usecase.execute(
        session_id=session_id,
        entity_id=entity_id,
        refresh_token=payload.refresh_token,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=EntityTokenRefreshData(
            token_type=result.token_type or "Bearer",
            access_token=result.access_token or "",
            access_token_expires_in=result.access_token_expires_in or 0,
            refresh_token=result.refresh_token or "",
            refresh_token_expires_in=result.refresh_token_expires_in or 0,
        ),
    )


@router.websocket("/{entity_id}/presence")
async def entity_presence(
    websocket: WebSocket,
    session_id: str,
    entity_id: str,
    access_token: str | None = Query(default=None),
    usecase: MaintainEntityPresenceUseCase = Depends(get_maintain_entity_presence_usecase),
    token_service: EntityTokenService = Depends(get_token_service),
    auth_state_repo: EntityAuthStateRepository = Depends(get_auth_state_repo),
) -> None:
    """维护 Entity Presence 长连接心跳。"""
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
        await validate_entity_access_token(
            token=access_token,
            session_id=session_id,
            entity_id=entity_id,
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
            entity_id=entity_id,
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
            "entity_id": entity_id,
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
                entity_id=entity_id,
                heartbeat_ttl_seconds=HEARTBEAT_TTL_SECONDS,
            )
            if message_type == "ping":
                await websocket.send_json({"type": "pong", "ts": int(time())})
    finally:
        await usecase.on_disconnect(session_id=session_id, entity_id=entity_id)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            with suppress(RuntimeError):
                await websocket.close(code=1000)
