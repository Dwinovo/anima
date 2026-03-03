from __future__ import annotations

from src.application.dto.agent import AgentContextResult
from src.application.dto.event import EventSearchItem
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository

DEFAULT_CONTEXT_LIMIT = 50
MAX_CONTEXT_SCAN_LIMIT = 500
CONTEXT_SCAN_MULTIPLIER = 4


class GetAgentContextUseCase:
    """读取 Agent 在社交平台中的相关上下文事件。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        presence_repo: AgentPresenceRepository,
        profile_repo: AgentProfileRepository,
        event_payload_repo: EventPayloadRepository,
        graph_event_repo: GraphEventRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._presence_repo = presence_repo
        self._profile_repo = profile_repo
        self._event_payload_repo = event_payload_repo
        self._graph_event_repo = graph_event_repo

    async def execute(
        self,
        *,
        session_id: str,
        agent_id: str,
        limit: int = DEFAULT_CONTEXT_LIMIT,
    ) -> AgentContextResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, agent_id=agent_id)
        is_active = await self._presence_repo.is_active(session_id=session_id, agent_id=agent_id)
        if profile_json is None and not is_active:
            raise AgentNotFoundException(session_id=session_id, uuid=agent_id)

        scan_limit = min(
            max(limit * CONTEXT_SCAN_MULTIPLIER, limit),
            MAX_CONTEXT_SCAN_LIMIT,
        )
        event_ids = await self._graph_event_repo.list_recent_event_ids(
            session_id=session_id,
            limit=scan_limit,
        )
        payload_map = await self._event_payload_repo.mget(event_ids=event_ids)

        ordered_items: list[EventSearchItem] = []
        for event_id in event_ids:
            payload = payload_map.get(event_id)
            if payload is None:
                continue
            ordered_items.append(self._to_search_item(event_id=event_id, payload=payload))

        current_world_time = ordered_items[0].world_time if ordered_items else 0
        followed_agent_ids = self._collect_followed_agent_ids(
            agent_id=agent_id,
            items=ordered_items,
        )
        self_event_ids = {
            item.event_id
            for item in ordered_items
            if item.subject_uuid == agent_id
        }

        status_events: list[EventSearchItem] = []
        media_public_events: list[EventSearchItem] = []
        media_following_events: list[EventSearchItem] = []
        self_events: list[EventSearchItem] = []
        for item in ordered_items:
            if item.subject_uuid == agent_id:
                self._append_with_limit(self_events, item, limit=limit)
                continue
            if self._is_status_event(
                item=item,
                agent_id=agent_id,
                self_event_ids=self_event_ids,
            ):
                self._append_with_limit(status_events, item, limit=limit)
                continue
            if item.subject_uuid in followed_agent_ids:
                self._append_with_limit(media_following_events, item, limit=limit)
                continue
            if self._is_public_media_event(item):
                self._append_with_limit(media_public_events, item, limit=limit)

        return AgentContextResult(
            session_id=session_id,
            agent_id=agent_id,
            current_world_time=current_world_time,
            status_events=status_events,
            media_public_events=media_public_events,
            media_following_events=media_following_events,
            self_events=self_events,
        )

    @staticmethod
    def _is_public_media_event(item: EventSearchItem) -> bool:
        """判断事件是否属于公共媒体流事件。"""
        if item.target_ref.startswith("board:"):
            return True
        return item.verb in {"POSTED", "REPLIED", "QUOTED"}

    @staticmethod
    def _append_with_limit(
        bucket: list[EventSearchItem],
        item: EventSearchItem,
        *,
        limit: int,
    ) -> None:
        """向目标桶追加事件，超出上限时忽略。"""
        if len(bucket) >= limit:
            return
        bucket.append(item)

    @staticmethod
    def _collect_followed_agent_ids(
        *,
        agent_id: str,
        items: list[EventSearchItem],
    ) -> set[str]:
        """从近期事件中提取当前 Agent 已关注对象集合。"""
        followed_agent_ids: set[str] = set()
        for item in items:
            if item.subject_uuid != agent_id:
                continue
            if item.verb != "FOLLOWED":
                continue
            target_agent_id = GetAgentContextUseCase._extract_agent_id_from_target_ref(item.target_ref)
            if target_agent_id is None:
                continue
            if target_agent_id == agent_id:
                continue
            followed_agent_ids.add(target_agent_id)
        return followed_agent_ids

    @staticmethod
    def _extract_agent_id_from_target_ref(target_ref: str) -> str | None:
        """将 target_ref 解析为 Agent ID。"""
        if not target_ref:
            return None
        if target_ref.startswith("board:"):
            return None
        if target_ref.startswith("event_"):
            return None
        if target_ref.startswith("agent:"):
            candidate = target_ref.split(":", maxsplit=1)[1]
            return candidate or None
        return target_ref

    @staticmethod
    def _is_status_event(
        *,
        item: EventSearchItem,
        agent_id: str,
        self_event_ids: set[str],
    ) -> bool:
        """判断事件是否属于“与我相关”的状态流。"""
        if item.target_ref == agent_id or item.target_ref == f"agent:{agent_id}":
            return True
        return item.target_ref in self_event_ids

    @staticmethod
    def _to_search_item(*, event_id: str, payload: dict[str, object]) -> EventSearchItem:
        """将载荷文档映射为统一事件 DTO。"""
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
