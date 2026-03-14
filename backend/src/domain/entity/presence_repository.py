from __future__ import annotations

from typing import Protocol


class EntityPresenceRepository(Protocol):
    """Entity 在线态仓储协议。"""

    async def is_active(self, *, session_id: str, entity_id: str) -> bool:
        """判断指定实体当前是否在线。"""
        ...

    async def count_active(self, *, session_id: str) -> int:
        """统计指定会话下的在线实体数量。"""
        ...

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出指定会话下所有在线实体 UUID。"""
        ...

    async def activate(self, *, session_id: str, entity_id: str) -> None:
        """将指定实体标记为在线状态。"""
        ...

    async def deactivate(self, *, session_id: str, entity_id: str) -> None:
        """将指定实体标记为离线状态。"""
        ...

    async def touch_heartbeat(
        self,
        *,
        session_id: str,
        entity_id: str,
        ttl_seconds: int,
    ) -> None:
        """刷新指定实体心跳 TTL。"""
        ...

    async def clear_heartbeat(self, *, session_id: str, entity_id: str) -> None:
        """清理指定实体心跳键。"""
        ...
