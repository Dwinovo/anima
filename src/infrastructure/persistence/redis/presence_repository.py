from __future__ import annotations

from src.domain.agent.presence_repository import AgentPresenceRepository
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.keys import active_agents_key


class RedisPresenceRepository(AgentPresenceRepository):
    """Redis 侧：Agent 在线态（Presence）仓储实现。"""

    def __init__(self, client: RedisClient) -> None:
        """初始化对象并注入所需依赖。"""
        self._client = client

    async def is_active(self, *, session_id: str, uuid: str) -> bool:
        """判断一个Agent在Session下是否是活跃的"""
        return await self._client.is_set_member(active_agents_key(session_id), uuid)

    async def count_active(self, *, session_id: str) -> int:
        """统计目前有多少个Agent活跃"""
        return await self._client.get_set_size(active_agents_key(session_id))

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出所有活跃的Agent"""
        return await self._client.get_set_members(active_agents_key(session_id))

    async def activate(self, *, session_id: str, uuid: str) -> None:
        """让某一个Agent活跃"""
        await self._client.add_set_member(active_agents_key(session_id), uuid)

    async def deactivate(self, *, session_id: str, uuid: str) -> None:
        """让某一个Agent不活跃"""
        await self._client.remove_set_member(active_agents_key(session_id), uuid)
