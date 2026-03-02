from __future__ import annotations

from typing import Any

from src.application.dto.event import EventSearchItem, EventSearchResult
from src.core.exceptions import SessionNotFoundException
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository


class SearchEventsUseCase:
    """执行 Event 检索（候选召回 -> 拓扑过滤 -> Mongo 水合）。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        event_payload_repo: EventPayloadRepository,
        graph_event_repo: GraphEventRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._event_payload_repo = event_payload_repo
        self._graph_event_repo = graph_event_repo

    async def execute(
        self,
        *,
        session_id: str,
        anchor_uuid: str,
        limit: int,
        candidate_limit: int,
    ) -> EventSearchResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        candidate_event_ids = await self._collect_candidate_event_ids(
            session_id=session_id,
            candidate_limit=candidate_limit,
        )
        if not candidate_event_ids:
            return EventSearchResult(session_id=session_id, items=[], total=0)

        filtered_event_ids = await self._graph_event_repo.topology_filter_event_ids(
            session_id=session_id,
            event_ids=candidate_event_ids,
            anchor_uuid=anchor_uuid,
            limit=limit,
        )
        if not filtered_event_ids:
            return EventSearchResult(session_id=session_id, items=[], total=0)

        payload_map = await self._event_payload_repo.mget(event_ids=filtered_event_ids)

        items: list[EventSearchItem] = []
        for event_id in filtered_event_ids:
            doc = payload_map.get(event_id)
            if doc is None:
                continue
            items.append(self._to_search_item(event_id=event_id, doc=doc))

        return EventSearchResult(
            session_id=session_id,
            items=items,
            total=len(items),
        )

    async def _collect_candidate_event_ids(
        self,
        *,
        session_id: str,
        candidate_limit: int,
    ) -> list[str]:
        """收集候选事件 ID（recent-only）。"""
        return await self._graph_event_repo.list_recent_event_ids(
            session_id=session_id,
            limit=candidate_limit,
        )

    @staticmethod
    def _to_search_item(*, event_id: str, doc: dict[str, Any]) -> EventSearchItem:
        """将 Mongo 文档映射为应用层 DTO。"""
        world_time = doc.get("world_time")
        schema_version = doc.get("schema_version")
        is_social = doc.get("is_social")
        details = doc.get("details")

        return EventSearchItem(
            event_id=event_id,
            world_time=world_time if isinstance(world_time, int) else 0,
            verb=doc.get("verb") if isinstance(doc.get("verb"), str) else "",
            subject_uuid=doc.get("subject_uuid") if isinstance(doc.get("subject_uuid"), str) else "",
            target_ref=doc.get("target_ref") if isinstance(doc.get("target_ref"), str) else "",
            details=details if isinstance(details, dict) else {},
            schema_version=schema_version if isinstance(schema_version, int) else 1,
            is_social=is_social if isinstance(is_social, bool) else False,
        )
