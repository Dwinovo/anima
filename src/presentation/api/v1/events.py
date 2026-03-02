from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.usecases.event.report_event import ReportEventUseCase
from src.presentation.api.constants.http_status import EVENT_ACCEPTED
from src.presentation.api.dependencies import get_report_event_usecase
from src.presentation.api.schemas.requests.event import EventReportRequest
from src.presentation.api.schemas.responses.envelope import ApiResponse
from src.presentation.api.schemas.responses.event import EventReportData

router = APIRouter(prefix="/sessions/{session_id}/events", tags=["events"])


@router.post(
    "",
    status_code=EVENT_ACCEPTED,
    response_model=ApiResponse[EventReportData],
    summary="Report event",
)
async def report_event(
    session_id: str,
    payload: EventReportRequest,
    usecase: ReportEventUseCase = Depends(get_report_event_usecase),
) -> ApiResponse[EventReportData]:
    """上报事件并触发骨肉双写。"""
    result = await usecase.execute(
        session_id=session_id,
        world_time=payload.world_time,
        subject_uuid=payload.subject.uuid,
        target_ref=payload.target.ref,
        verb=payload.action.verb,
        details=payload.action.details,
        schema_version=payload.schema_version,
        is_social=payload.action.is_social,
        embedding_256=payload.embedding_256,
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
