from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.get_session import GetSessionUseCase
from src.application.usecases.session.list_sessions import (
    ListSessionsUseCase,
)
from src.application.usecases.session.patch_session import PatchSessionUseCase
from src.presentation.api.constants.http_status import (
    HTTP_200_OK,
    SESSION_CREATED,
    SESSION_DELETED,
)
from src.presentation.api.dependencies import (
    get_create_session_usecase,
    get_delete_session_usecase,
    get_get_session_usecase,
    get_list_sessions_usecase,
    get_patch_session_usecase,
)
from src.presentation.api.schemas.requests.session import (
    SessionCreateRequest,
    SessionPatchRequest,
)
from src.presentation.api.schemas.responses.envelope import ApiResponse
from src.presentation.api.schemas.responses.session import (
    SessionCreateData,
    SessionDetailData,
    SessionListData,
    SessionListItem,
)
from src.presentation.api.schemas.session_action import SessionActionSchema

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_action_items(actions: tuple[object, ...] | list[object]) -> list[SessionActionSchema]:
    """将领域动作对象映射为响应模型。"""
    return [SessionActionSchema.from_domain(action) for action in actions]


@router.post(
    "",
    status_code=SESSION_CREATED,
    response_model=ApiResponse[SessionCreateData],
    summary="Create session",
)
async def create_session(
    payload: SessionCreateRequest,
    usecase: CreateSessionUseCase = Depends(get_create_session_usecase),
) -> ApiResponse[SessionCreateData]:
    """创建资源并返回创建结果。"""
    session = await usecase.execute(
        name=payload.name,
        description=payload.description,
        max_entities_limit=payload.max_entities_limit,
        actions=[item.model_dump() for item in payload.actions],
    )
    data = SessionCreateData(
        session_id=session.session_id,
        name=session.name,
        description=session.description,
        max_entities_limit=session.max_entities_limit,
        actions=_to_action_items(session.actions),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )

    return ApiResponse(
        code=0,
        message="success",
        data=data,
    )


@router.get(
    "",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[SessionListData],
    summary="List sessions",
)
async def list_sessions(
    usecase: ListSessionsUseCase = Depends(get_list_sessions_usecase),
) -> ApiResponse[SessionListData]:
    """列出 PostgreSQL 控制面中的全部会话列表。"""
    sessions = await usecase.execute()
    items = [
        SessionListItem(
            session_id=item.session_id,
            name=item.name,
            description=item.description,
            max_entities_limit=item.max_entities_limit,
        )
        for item in sessions
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=SessionListData(items=items, total=len(items)),
    )


@router.get(
    "/{session_id}",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[SessionDetailData],
    summary="Get session",
)
async def get_session(
    session_id: str,
    usecase: GetSessionUseCase = Depends(get_get_session_usecase),
) -> ApiResponse[SessionDetailData]:
    """获取指定 Session 详情。"""
    session = await usecase.execute(session_id=session_id)
    return ApiResponse(
        code=0,
        message="success",
        data=SessionDetailData(
            session_id=session.session_id,
            name=session.name,
            description=session.description,
            max_entities_limit=session.max_entities_limit,
            actions=_to_action_items(session.actions),
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
    )


@router.patch(
    "/{session_id}",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[SessionDetailData],
    summary="Patch session",
)
async def patch_session(
    session_id: str,
    payload: SessionPatchRequest,
    usecase: PatchSessionUseCase = Depends(get_patch_session_usecase),
) -> ApiResponse[SessionDetailData]:
    """增量更新指定 Session。"""
    session = await usecase.execute(
        session_id=session_id,
        name=payload.name,
        description=payload.description,
        max_entities_limit=payload.max_entities_limit,
        actions=[item.model_dump() for item in payload.actions] if payload.actions is not None else None,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=SessionDetailData(
            session_id=session.session_id,
            name=session.name,
            description=session.description,
            max_entities_limit=session.max_entities_limit,
            actions=_to_action_items(session.actions),
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
    )


@router.delete(
    "/{session_id}",
    status_code=SESSION_DELETED,
    summary="Delete session",
    response_class=Response,
)
async def delete_session(
    session_id: str,
    usecase: DeleteSessionUseCase = Depends(get_delete_session_usecase),
) -> Response:
    """删除指定资源。"""
    await usecase.execute(session_id=session_id)
    return Response(status_code=SESSION_DELETED)
