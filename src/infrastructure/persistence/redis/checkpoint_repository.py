from __future__ import annotations

import json

from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from src.domain.agent.checkpoint_repository import AgentCheckpointRepository
from src.infrastructure.persistence.redis.client import RedisClient
from src.infrastructure.persistence.redis.keys import checkpoint_key


class RedisCheckpointRepository(AgentCheckpointRepository):
    """Redis 侧：LangGraph 短期记忆快照仓储实现。"""

    def __init__(
        self,
        client: RedisClient,
        *,
        langgraph_checkpointer: AsyncRedisSaver | None = None,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._client = client
        self._langgraph_checkpointer = langgraph_checkpointer

    async def load(self, *, session_id: str, uuid: str) -> list[str]:
        """读取 Agent 的短期记忆快照。"""
        raw_value = await self._client.get_value(checkpoint_key(session_id, uuid))
        if raw_value is None:
            return []
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, str)]

    async def save(
        self,
        *,
        session_id: str,
        uuid: str,
        snapshots: list[str],
        ttl_seconds: int,
    ) -> None:
        """写入 Agent 的短期记忆快照并设置过期时间。"""
        payload = json.dumps(snapshots, ensure_ascii=False, separators=(",", ":"))
        await self._client.set_value(
            checkpoint_key(session_id, uuid),
            payload,
            ttl_seconds=ttl_seconds,
        )

    async def clear(self, *, session_id: str, uuid: str) -> None:
        """删除 Agent 的短期记忆快照。"""
        await self._client.delete_key(checkpoint_key(session_id, uuid))
        if self._langgraph_checkpointer is not None:
            await self._langgraph_checkpointer.adelete_thread(f"{session_id}:{uuid}")
