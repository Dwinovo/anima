from __future__ import annotations

from src.domain.agent.profile_repository import AgentProfileRepository
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.keys import agent_profile_key, display_name_key


class RedisProfileRepository(AgentProfileRepository):
    """Redis 侧：Agent Profile（系统提示词字符串）仓储实现。"""

    def __init__(self, client: RedisClient) -> None:
        """初始化对象并注入所需依赖。"""
        self._client = client

    async def save(
        self,
        *,
        session_id: str,
        uuid: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """保存目标数据。"""
        await self._client.set_value(
            agent_profile_key(session_id, uuid),
            profile_json,
            ttl_seconds=ttl_seconds,
        )

    async def get(self, *, session_id: str, uuid: str) -> str | None:
        """执行 `get` 相关逻辑。"""
        return await self._client.get_value(agent_profile_key(session_id, uuid))

    async def delete(self, *, session_id: str, uuid: str) -> None:
        """删除指定资源。"""
        await self._client.delete_key(agent_profile_key(session_id, uuid))

    async def claim_display_name(
        self,
        *,
        session_id: str,
        uuid: str,
        display_name: str,
    ) -> bool:
        """尝试占用展示名，若已被自己占用则视为成功。"""
        key = display_name_key(session_id, display_name)
        claimed = await self._client.set_value_if_absent(key, uuid)
        if claimed:
            return True
        existing = await self._client.get_value(key)
        return existing == uuid

    async def release_display_name(
        self,
        *,
        session_id: str,
        uuid: str,
        display_name: str,
    ) -> None:
        """仅当展示名属于当前实体时释放占用。"""
        key = display_name_key(session_id, display_name)
        existing = await self._client.get_value(key)
        if existing != uuid:
            return
        await self._client.delete_key(key)
