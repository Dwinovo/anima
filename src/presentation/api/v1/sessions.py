from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.list_sessions import (
    ListSessionsUseCase,
)
from src.presentation.api.constants.http_status import (
    HTTP_200_OK,
    SESSION_CREATED,
    SESSION_DELETED,
)
from src.presentation.api.dependencies import (
    get_create_session_usecase,
    get_delete_session_usecase,
    get_list_sessions_usecase,
)
from src.presentation.api.schemas.requests.session import SessionCreateRequest
from src.presentation.api.schemas.responses.envelope import ApiResponse
from src.presentation.api.schemas.responses.session import (
    SessionCreateData,
    SessionListData,
    SessionListItem,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


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
        max_agents_limit=payload.max_agents_limit,
        default_llm=payload.default_llm,
    )
    data = SessionCreateData(
        session_id=session.session_id,
        name=session.name,
        description=session.description,
        max_agents_limit=session.max_agents_limit,
        default_llm=session.default_llm,
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
            max_agents_limit=item.max_agents_limit,
        )
        for item in sessions
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=SessionListData(items=items, total=len(items)),
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
