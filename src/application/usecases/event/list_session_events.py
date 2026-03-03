from __future__ import annotations

from src.application.dto.event import EventListResult, EventSearchItem
from src.core.exceptions import SessionNotFoundException
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository


class ListSessionEventsUseCase:
    """列出指定会话的事件流（按时间倒序，支持游标翻页）。"""

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
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
    ) -> EventListResult:
        """执行会话事件列表查询并返回分页结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        fetch_limit = limit + 1
        recent_event_ids = await self._graph_event_repo.list_recent_event_ids(
            session_id=session_id,
            limit=fetch_limit,
            before_world_time=before_world_time,
            before_event_id=before_event_id,
        )

        has_more = len(recent_event_ids) > limit
        page_event_ids = recent_event_ids[:limit]
        if not page_event_ids:
            return EventListResult(
                session_id=session_id,
                items=[],
                next_cursor=None,
                has_more=False,
            )

        payload_map = await self._event_payload_repo.mget(event_ids=page_event_ids)
        items: list[EventSearchItem] = []
        for event_id in page_event_ids:
            payload = payload_map.get(event_id)
            if payload is None:
                continue
            items.append(self._to_search_item(event_id=event_id, payload=payload))

        next_cursor = self._build_next_cursor(items=items) if has_more else None
        return EventListResult(
            session_id=session_id,
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _build_next_cursor(*, items: list[EventSearchItem]) -> str | None:
        """根据当前页最后一条记录构造下一页游标。"""
        if not items:
            return None
        last_item = items[-1]
        return f"{last_item.world_time}:{last_item.event_id}"

    @staticmethod
    def _to_search_item(*, event_id: str, payload: dict[str, object]) -> EventSearchItem:
        """将载荷文档映射为统一事件检索 DTO。"""
        world_time = payload.get("world_time")
        verb = payload.get("verb")
        subject_uuid = payload.get("subject_uuid")
        target_ref = payload.get("target_ref")
        details = payload.get("details")
        schema_version = payload.get("schema_version")
        is_social = payload.get("is_social")
        return EventSearchItem(
            event_id=event_id,
            world_time=world_time if isinstance(world_time, int) else 0,
            verb=verb if isinstance(verb, str) else "",
            subject_uuid=subject_uuid if isinstance(subject_uuid, str) else "",
            target_ref=target_ref if isinstance(target_ref, str) else "",
            details=details if isinstance(details, dict) else {},
            schema_version=schema_version if isinstance(schema_version, int) else 1,
            is_social=is_social if isinstance(is_social, bool) else False,
        )
