from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.application.dto.event import EventReportResult
from src.core.exceptions import EntityNotFoundException, SessionNotFoundException
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository


class ReportEventUseCase:
    """处理 Event 上报并执行骨肉双写。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        profile_repo: EntityProfileRepository,
        event_payload_repo: EventPayloadRepository,
        graph_event_repo: GraphEventRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._profile_repo = profile_repo
        self._event_payload_repo = event_payload_repo
        self._graph_event_repo = graph_event_repo

    async def execute(
        self,
        *,
        session_id: str,
        world_time: int,
        subject_uuid: str,
        target_ref: str,
        verb: str,
        details: dict[str, Any],
        schema_version: int,
    ) -> EventReportResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)
        subject_profile = await self._profile_repo.get(
            session_id=session_id,
            entity_id=subject_uuid,
        )
        if subject_profile is None:
            raise EntityNotFoundException(session_id=session_id, uuid=subject_uuid)

        event_id = f"event_{uuid4().hex}"
        # 先写载荷（Mongo），再写骨架（Neo4j），遵循规范中的双写顺序。
        await self._event_payload_repo.put(
            event_id=event_id,
            doc={
                "session_id": session_id,
                "world_time": world_time,
                "verb": verb,
                "subject_uuid": subject_uuid,
                "target_ref": target_ref,
                "details": details,
                "schema_version": schema_version,
            },
        )
        await self._graph_event_repo.upsert_event(
            session_id=session_id,
            event_id=event_id,
            world_time=world_time,
            verb=verb,
            subject_uuid=subject_uuid,
            target_ref=target_ref,
        )
        return EventReportResult(
            session_id=session_id,
            event_id=event_id,
            world_time=world_time,
            verb=verb,
            accepted=True,
        )
