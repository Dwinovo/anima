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

        event_ids = await self._graph_event_repo.list_recent_event_ids(
            session_id=session_id,
            limit=limit,
        )
        payload_map = await self._event_payload_repo.mget(event_ids=event_ids)

        status_events: list[EventSearchItem] = []
        media_events: list[EventSearchItem] = []
        for event_id in event_ids:
            payload = payload_map.get(event_id)
            if payload is None:
                continue
            item = self._to_search_item(event_id=event_id, payload=payload)
            if self._is_media_event(item):
                media_events.append(item)
            else:
                status_events.append(item)

        return AgentContextResult(
            session_id=session_id,
            agent_id=agent_id,
            status_events=status_events,
            media_events=media_events,
        )

    @staticmethod
    def _is_media_event(item: EventSearchItem) -> bool:
        """判断事件是否属于媒体流事件。"""
        if item.target_ref.startswith("board:"):
            return True
        return item.verb in {"POSTED", "REPLIED", "QUOTED"}

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
