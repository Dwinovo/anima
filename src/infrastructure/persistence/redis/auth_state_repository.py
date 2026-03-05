from __future__ import annotations

from src.domain.entity.auth_state_repository import EntityAuthStateRepository
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.keys import (
    auth_refresh_index_key,
    auth_refresh_token_key,
    auth_token_version_key,
)


class RedisAuthStateRepository(EntityAuthStateRepository):
    """Redis 侧：Entity 鉴权状态仓储实现。"""

    def __init__(self, client: RedisClient) -> None:
        """初始化对象并注入所需依赖。"""
        self._client = client

    async def ensure_token_version(
        self,
        *,
        session_id: str,
        entity_id: str,
        initial_version: int = 1,
    ) -> int:
        """确保 token_version 存在并返回当前值。"""
        key = auth_token_version_key(session_id, entity_id)
        created = await self._client.set_value_if_absent(key, str(initial_version))
        if created:
            return initial_version
        existing = await self._client.get_value(key)
        if existing is None:
            await self._client.set_value(key, str(initial_version))
            return initial_version
        try:
            return int(existing)
        except ValueError:
            await self._client.set_value(key, str(initial_version))
            return initial_version

    async def get_token_version(self, *, session_id: str, entity_id: str) -> int | None:
        """读取 token_version。"""
        existing = await self._client.get_value(auth_token_version_key(session_id, entity_id))
        if existing is None:
            return None
        try:
            return int(existing)
        except ValueError:
            return None

    async def bump_token_version(self, *, session_id: str, entity_id: str) -> int:
        """提升 token_version 并返回新值。"""
        return await self._client.incr_value(auth_token_version_key(session_id, entity_id))

    async def store_refresh_jti(
        self,
        *,
        session_id: str,
        entity_id: str,
        refresh_jti: str,
        ttl_seconds: int,
    ) -> None:
        """存储 refresh_jti。"""
        token_key = auth_refresh_token_key(session_id, entity_id, refresh_jti)
        index_key = auth_refresh_index_key(session_id, entity_id)
        await self._client.set_value(token_key, "1", ttl_seconds=ttl_seconds)
        await self._client.add_set_member(index_key, refresh_jti)

    async def consume_refresh_jti(
        self,
        *,
        session_id: str,
        entity_id: str,
        refresh_jti: str,
    ) -> bool:
        """消费 refresh_jti（单次生效）。"""
        token_key = auth_refresh_token_key(session_id, entity_id, refresh_jti)
        value = await self._client.get_and_delete(token_key)
        await self._client.remove_set_member(
            auth_refresh_index_key(session_id, entity_id),
            refresh_jti,
        )
        return value is not None

    async def revoke_all_refresh_jti(self, *, session_id: str, entity_id: str) -> None:
        """撤销指定 Entity 的全部 refresh_jti。"""
        index_key = auth_refresh_index_key(session_id, entity_id)
        jti_list = await self._client.get_set_members(index_key)
        keys = [auth_refresh_token_key(session_id, entity_id, refresh_jti) for refresh_jti in jti_list]
        await self._client.delete_keys(keys)
        await self._client.delete_key(index_key)
