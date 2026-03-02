from __future__ import annotations

import pytest

from src.infrastructure.persistence.redis.checkpoint_repository import RedisCheckpointRepository
from src.infrastructure.persistence.redis.keys import checkpoint_key


class FakeRedisClient:
    """RedisClient 测试替身。"""

    def __init__(self) -> None:
        """初始化内存态存储。"""
        self._data: dict[str, str] = {}
        self.deleted_keys: list[str] = []

    async def get_value(self, key: str) -> str | None:
        """读取字符串键值。"""
        return self._data.get(key)

    async def set_value(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """写入字符串键值。"""
        _ = ttl_seconds
        self._data[key] = value

    async def delete_key(self, key: str) -> int:
        """删除键并记录。"""
        self.deleted_keys.append(key)
        existed = 1 if key in self._data else 0
        self._data.pop(key, None)
        return existed


class FakeLangGraphCheckpointer:
    """LangGraph Checkpointer 测试替身。"""

    def __init__(self) -> None:
        """初始化调用记录。"""
        self.deleted_threads: list[str] = []

    async def adelete_thread(self, thread_id: str) -> None:
        """记录线程删除请求。"""
        self.deleted_threads.append(thread_id)


@pytest.mark.asyncio
async def test_checkpoint_repository_clear_removes_manual_key_and_langgraph_thread() -> None:
    """验证 clear 会同时清理手写快照键与 LangGraph 线程快照。"""
    redis_client = FakeRedisClient()
    checkpointer = FakeLangGraphCheckpointer()
    repository = RedisCheckpointRepository(
        redis_client,
        langgraph_checkpointer=checkpointer,
    )
    key = checkpoint_key("session_demo", "agent_a")
    await redis_client.set_value(key, '["记忆A"]')

    await repository.clear(session_id="session_demo", uuid="agent_a")

    assert redis_client.deleted_keys == [key]
    assert checkpointer.deleted_threads == ["session_demo:agent_a"]
