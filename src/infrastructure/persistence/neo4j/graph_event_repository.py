from __future__ import annotations

from neo4j import AsyncDriver

from src.domain.memory.graph_event_repository import GraphEventRepository
from src.infrastructure.persistence.neo4j.cypher import (
    RECENT_EVENT_IDS,
    UPSERT_EVENT,
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
        async with self._driver.session() as session:
            await session.run(
                UPSERT_EVENT,
                {
                    "session_id": session_id,
                    "event_id": event_id,
                    "world_time": world_time,
                    "verb": verb,
                    "subject_uuid": subject_uuid,
                    "target_ref": target_ref,
                },
            )

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
    ) -> list[str]:
        """按时间倒序获取近期事件候选。"""
        async with self._driver.session() as session:
            result = await session.run(
                RECENT_EVENT_IDS,
                {
                    "session_id": session_id,
                    "limit": limit,
                    "before_world_time": before_world_time,
                    "before_event_id": before_event_id,
                },
            )
            rows = await result.data()

        return [r["event_id"] for r in rows]
