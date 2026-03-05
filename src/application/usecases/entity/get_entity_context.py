from __future__ import annotations

from dataclasses import dataclass, field

from src.application.dto.entity import (
    EntityContextEventListView,
    EntityContextHotListView,
    EntityContextHotTopic,
    EntityContextResult,
    EntityContextViews,
    EntityContextWorldSnapshot,
)
from src.application.dto.event import EventSearchItem
from src.core.exceptions import EntityNotFoundException, SessionNotFoundException
from src.domain.entity.presence_repository import EntityPresenceRepository
from src.domain.entity.profile_repository import EntityProfileRepository
from src.domain.memory.event_payload_repository import EventPayloadRepository
from src.domain.memory.graph_event_repository import GraphEventRepository
from src.domain.session.repository import SessionRepository

DEFAULT_CONTEXT_LIMIT = 50
MAX_CONTEXT_SCAN_LIMIT = 500
CONTEXT_SCAN_MULTIPLIER = 4


@dataclass(slots=True)
class _HotTopicAccumulator:
    """热点聚合临时结构。"""

    count: int = 0
    latest_world_time: int = 0
    sample_event_ids: list[str] = field(default_factory=list)


class GetEntityContextUseCase:
    """读取 Entity 在当前 Session 的 Activity 上下文事件。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        presence_repo: EntityPresenceRepository,
        profile_repo: EntityProfileRepository,
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
        entity_id: str,
        limit: int = DEFAULT_CONTEXT_LIMIT,
    ) -> EntityContextResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, entity_id=entity_id)
        is_active = await self._presence_repo.is_active(session_id=session_id, entity_id=entity_id)
        if profile_json is None and not is_active:
            raise EntityNotFoundException(session_id=session_id, uuid=entity_id)

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
        followed_entity_ids = self._collect_followed_entity_ids(
            entity_id=entity_id,
            items=ordered_items,
        )
        self_event_ids = {
            item.event_id
            for item in ordered_items
            if item.subject_uuid == entity_id
        }

        self_recent_events: list[EventSearchItem] = []
        public_feed_events: list[EventSearchItem] = []
        following_feed_events: list[EventSearchItem] = []
        attention_events: list[EventSearchItem] = []
        for item in ordered_items:
            if item.subject_uuid == entity_id:
                self_recent_events.append(item)
                continue
            if self._is_status_event(
                item=item,
                entity_id=entity_id,
                self_event_ids=self_event_ids,
            ):
                attention_events.append(item)
                continue
            if item.subject_uuid in followed_entity_ids:
                following_feed_events.append(item)
                continue
            if self._is_public_media_event(item):
                public_feed_events.append(item)

        active_count = await self._presence_repo.count_active(session_id=session_id)
        hot_topics = self._build_hot_topics(items=ordered_items)

        return EntityContextResult(
            session_id=session_id,
            entity_id=entity_id,
            current_world_time=current_world_time,
            views=EntityContextViews(
                self_recent=self._build_event_view(items=self_recent_events, limit=limit),
                public_feed=self._build_event_view(items=public_feed_events, limit=limit),
                following_feed=self._build_event_view(items=following_feed_events, limit=limit),
                attention=self._build_event_view(items=attention_events, limit=limit),
                hot=self._build_hot_view(items=hot_topics, limit=limit),
                world_snapshot=EntityContextWorldSnapshot(
                    online_entities=active_count,
                    active_entities=active_count,
                    recent_event_count=len(ordered_items),
                    my_following_count=len(followed_entity_ids),
                ),
            ),
        )

    @staticmethod
    def _is_public_media_event(item: EventSearchItem) -> bool:
        """判断事件是否属于公共媒体流事件。"""
        if item.target_ref.startswith("board:"):
            return True
        return item.verb in {"social.posted", "social.replied", "social.quoted"}

    @staticmethod
    def _build_event_view(
        *,
        items: list[EventSearchItem],
        limit: int,
    ) -> EntityContextEventListView:
        """构建统一的事件流视图结构。"""
        visible_items = items[:limit]
        has_more = len(items) > limit
        next_cursor = None
        if has_more and visible_items:
            next_cursor = GetEntityContextUseCase._build_event_cursor(visible_items[-1])
        return EntityContextEventListView(
            items=visible_items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _build_hot_topics(*, items: list[EventSearchItem]) -> list[EntityContextHotTopic]:
        """按 target_ref 聚合热点并按热度排序。"""
        topic_map: dict[str, _HotTopicAccumulator] = {}
        for item in items:
            topic_ref = item.target_ref.strip()
            if topic_ref == "":
                continue
            acc = topic_map.get(topic_ref)
            if acc is None:
                acc = _HotTopicAccumulator()
                topic_map[topic_ref] = acc
            acc.count += 1
            if item.world_time > acc.latest_world_time:
                acc.latest_world_time = item.world_time
            if len(acc.sample_event_ids) < 3:
                acc.sample_event_ids.append(item.event_id)

        ranked_topics = sorted(
            topic_map.items(),
            key=lambda pair: (-pair[1].count, -pair[1].latest_world_time, pair[0]),
        )
        return [
            EntityContextHotTopic(
                topic_ref=topic_ref,
                score=float(acc.count),
                sample_event_ids=list(acc.sample_event_ids),
            )
            for topic_ref, acc in ranked_topics
        ]

    @staticmethod
    def _build_hot_view(
        *,
        items: list[EntityContextHotTopic],
        limit: int,
    ) -> EntityContextHotListView:
        """构建热点视图结构。"""
        visible_items = items[:limit]
        has_more = len(items) > limit
        next_cursor = None
        if has_more and visible_items:
            next_cursor = visible_items[-1].topic_ref
        return EntityContextHotListView(
            items=visible_items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _build_event_cursor(item: EventSearchItem) -> str:
        """按事件生成分页游标。"""
        return f"{item.world_time}:{item.event_id}"

    @staticmethod
    def _collect_followed_entity_ids(
        *,
        entity_id: str,
        items: list[EventSearchItem],
    ) -> set[str]:
        """从近期事件中提取当前 Entity 已关注对象集合。"""
        followed_entity_ids: set[str] = set()
        for item in items:
            if item.subject_uuid != entity_id:
                continue
            if item.verb != "social.followed":
                continue
            target_entity_id = GetEntityContextUseCase._extract_entity_id_from_target_ref(item.target_ref)
            if target_entity_id is None:
                continue
            if target_entity_id == entity_id:
                continue
            followed_entity_ids.add(target_entity_id)
        return followed_entity_ids

    @staticmethod
    def _extract_entity_id_from_target_ref(target_ref: str) -> str | None:
        """将 target_ref 解析为 Entity ID。"""
        if not target_ref:
            return None
        if target_ref.startswith("board:"):
            return None
        if target_ref.startswith("event_"):
            return None
        if target_ref.startswith("entity:"):
            candidate = target_ref.split(":", maxsplit=1)[1]
            return candidate or None
        return target_ref

    @staticmethod
    def _is_status_event(
        *,
        item: EventSearchItem,
        entity_id: str,
        self_event_ids: set[str],
    ) -> bool:
        """判断事件是否属于“与我相关”的状态流。"""
        if item.target_ref == entity_id or item.target_ref == f"entity:{entity_id}":
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
        return EventSearchItem(
            event_id=event_id,
            world_time=world_time if isinstance(world_time, int) else 0,
            verb=verb if isinstance(verb, str) else "",
            subject_uuid=subject_uuid if isinstance(subject_uuid, str) else "",
            target_ref=target_ref if isinstance(target_ref, str) else "",
            details=details if isinstance(details, dict) else {},
            schema_version=schema_version if isinstance(schema_version, int) else 1,
        )
