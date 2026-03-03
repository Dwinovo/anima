from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.usecases.event.list_session_events import ListSessionEventsUseCase
from src.application.usecases.event.report_event import ReportEventUseCase
from src.core.exceptions import AuthorizationDeniedException
from src.domain.agent.token_service import TokenClaims
from src.presentation.api.constants.http_status import EVENT_ACCEPTED, HTTP_200_OK
from src.presentation.api.dependencies import (
    get_list_session_events_usecase,
    get_report_event_usecase,
    require_session_access_claims,
)
from src.presentation.api.schemas.requests.event import EventListQuery, EventReportRequest
from src.presentation.api.schemas.responses.envelope import ApiResponse
from src.presentation.api.schemas.responses.event import (
    EventListData,
    EventListItem,
    EventReportData,
)

router = APIRouter(prefix="/sessions/{session_id}/events", tags=["events"])


@router.get(
    "",
    status_code=HTTP_200_OK,
    response_model=ApiResponse[EventListData],
    summary="List session events",
)
async def list_session_events(
    session_id: str,
    query: EventListQuery = Depends(),
    usecase: ListSessionEventsUseCase = Depends(get_list_session_events_usecase),
) -> ApiResponse[EventListData]:
    """按时间倒序列出会话事件流。"""
    before_world_time, before_event_id = query.parse_cursor()
    result = await usecase.execute(
        session_id=session_id,
        limit=query.limit,
        before_world_time=before_world_time,
        before_event_id=before_event_id,
    )
    items = [
        EventListItem(
            event_id=item.event_id,
            world_time=item.world_time,
            verb=item.verb,
            subject_uuid=item.subject_uuid,
            target_ref=item.target_ref,
            details=item.details,
            schema_version=item.schema_version,
            is_social=item.is_social,
        )
        for item in result.items
    ]
    return ApiResponse(
        code=0,
        message="success",
        data=EventListData(
            items=items,
            next_cursor=result.next_cursor,
            has_more=result.has_more,
        ),
    )


@router.post(
    "",
    status_code=EVENT_ACCEPTED,
    response_model=ApiResponse[EventReportData],
    summary="Report event",
)
async def report_event(
    session_id: str,
    payload: EventReportRequest,
    claims: TokenClaims = Depends(require_session_access_claims),
    usecase: ReportEventUseCase = Depends(get_report_event_usecase),
) -> ApiResponse[EventReportData]:
    """上报事件并触发骨肉双写。"""
    if claims.agent_id != payload.subject_uuid:
        raise AuthorizationDeniedException("Token subject does not match subject_uuid.")
    result = await usecase.execute(
        session_id=session_id,
        world_time=payload.world_time,
        subject_uuid=payload.subject_uuid,
        target_ref=payload.target_ref,
        verb=payload.verb,
        details=payload.details,
        schema_version=payload.schema_version,
        is_social=payload.is_social,
    )
    return ApiResponse(
        code=0,
        message="success",
        data=EventReportData(
            session_id=result.session_id,
            event_id=result.event_id,
            world_time=result.world_time,
            verb=result.verb,
            accepted=result.accepted,
        ),
    )
