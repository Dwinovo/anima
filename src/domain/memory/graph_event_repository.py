from __future__ import annotations

from typing import Protocol


class GraphEventRepository(Protocol):
    """图谱记忆仓储（仅存骨架与向量指针）"""

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
        embedding_256: list[float] | None,
        is_social: bool,
    ) -> None:
        """写入事件骨架（惰性建点 + 关系建立）"""

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
    ) -> list[str]:
        """按时间倒序列出近期事件候选（recent-only）"""

    async def topology_filter_event_ids(
        self,
        *,
        session_id: str,
        event_ids: list[str],
        anchor_uuid: str,
        limit: int,
    ) -> list[str]:
        """图谱拓扑过滤（第二阶段）"""
