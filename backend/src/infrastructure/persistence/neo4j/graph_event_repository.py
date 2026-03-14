from __future__ import annotations

from neo4j import AsyncDriver

from src.domain.memory.graph_event_repository import GraphEventRepository
from src.infrastructure.persistence.neo4j.cypher import (
    RECENT_EVENT_IDS,
    UPSERT_EVENT_TARGET_ENTITY,
    UPSERT_EVENT_TARGET_OBJECT,
)


class Neo4jGraphEventRepository(GraphEventRepository):
    """Neo4j 图谱骨架实现"""

    def __init__(self, driver: AsyncDriver) -> None:
        """初始化对象并注入所需依赖。"""
        self._driver = driver

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
    ) -> None:
        """写入或更新目标数据。"""
        subject_ref = self._to_entity_ref(subject_uuid)
        target_entity_ref = self._extract_target_entity_ref(target_ref)
        query = UPSERT_EVENT_TARGET_OBJECT
        params: dict[str, str | int] = {
            "session_id": session_id,
            "event_id": event_id,
            "world_time": world_time,
            "verb": verb,
            "subject_ref": subject_ref,
            "target_ref": target_ref,
        }
        if target_entity_ref is not None:
            query = UPSERT_EVENT_TARGET_ENTITY
            params = {
                "session_id": session_id,
                "event_id": event_id,
                "world_time": world_time,
                "verb": verb,
                "subject_ref": subject_ref,
                "target_entity_ref": target_entity_ref,
            }
        async with self._driver.session() as session:
            await session.run(query, params)

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
        verb_domain: str | None = None,
    ) -> list[str]:
        """按时间倒序获取近期事件候选。"""
        verb_prefix = f"{verb_domain}." if verb_domain is not None else None
        async with self._driver.session() as session:
            result = await session.run(
                RECENT_EVENT_IDS,
                {
                    "session_id": session_id,
                    "limit": limit,
                    "before_world_time": before_world_time,
                    "before_event_id": before_event_id,
                    "verb_prefix": verb_prefix,
                },
            )
            rows = await result.data()

        return [r["event_id"] for r in rows]

    @staticmethod
    def _to_entity_ref(raw_id: str) -> str:
        """将输入实体标识归一化为 entity:<id>。"""
        if raw_id.startswith("entity:"):
            return raw_id
        if raw_id.startswith("entity:"):
            candidate = raw_id.split(":", maxsplit=1)[1]
            return f"entity:{candidate}"
        return f"entity:{raw_id}"

    @classmethod
    def _extract_target_entity_ref(cls, target_ref: str) -> str | None:
        """从 target_ref 提取目标实体引用（entity:<id>），无法判定为实体时返回 None。"""
        if target_ref.startswith("entity:") or target_ref.startswith("entity:"):
            return cls._to_entity_ref(target_ref)
        if target_ref.startswith("board:") or target_ref.startswith("event_"):
            return None
        if ":" in target_ref:
            return None
        return cls._to_entity_ref(target_ref) if target_ref else None
