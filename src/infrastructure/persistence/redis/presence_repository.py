from __future__ import annotations

from src.domain.entity.presence_repository import EntityPresenceRepository
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.keys import active_entities_key, heartbeat_key


class RedisPresenceRepository(EntityPresenceRepository):
    """Redis 侧：Entity 在线态（Presence）仓储实现。"""

    def __init__(self, client: RedisClient) -> None:
        """初始化对象并注入所需依赖。"""
        self._client = client

    async def is_active(self, *, session_id: str, entity_id: str) -> bool:
        """判断一个Entity在Session下是否是活跃的"""
        return await self._client.is_set_member(active_entities_key(session_id), entity_id)

    async def count_active(self, *, session_id: str) -> int:
        """统计目前有多少个Entity活跃"""
        return await self._client.get_set_size(active_entities_key(session_id))

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出所有活跃的Entity"""
        return await self._client.get_set_members(active_entities_key(session_id))

    async def activate(self, *, session_id: str, entity_id: str) -> None:
        """让某一个Entity活跃"""
        await self._client.add_set_member(active_entities_key(session_id), entity_id)

    async def deactivate(self, *, session_id: str, entity_id: str) -> None:
        """让某一个Entity不活跃"""
        await self._client.remove_set_member(active_entities_key(session_id), entity_id)

    async def touch_heartbeat(
        self,
        *,
        session_id: str,
        entity_id: str,
        ttl_seconds: int,
    ) -> None:
        """刷新 Entity 心跳 TTL。"""
        await self._client.set_value(
            heartbeat_key(session_id, entity_id),
            "1",
            ttl_seconds=ttl_seconds,
        )

    async def clear_heartbeat(self, *, session_id: str, entity_id: str) -> None:
        """清理 Entity 心跳键。"""
        await self._client.delete_key(heartbeat_key(session_id, entity_id))
