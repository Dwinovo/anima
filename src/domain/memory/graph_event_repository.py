from __future__ import annotations

from typing import Protocol


class GraphEventRepository(Protocol):
    """图谱记忆仓储（仅存轻量骨架拓扑）"""

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
        is_social: bool,
    ) -> None:
        """写入事件骨架（惰性建点 + 关系建立）"""

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
    ) -> list[str]:
        """按时间倒序列出近期事件候选（recent-only）"""
