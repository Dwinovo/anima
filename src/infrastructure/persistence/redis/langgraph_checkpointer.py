from __future__ import annotations

import math
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.redis.aio import AsyncRedisSaver


@asynccontextmanager
async def create_langgraph_checkpointer(
    *,
    redis_url: str,
    ttl_seconds: int,
    refresh_on_read: bool = True,
    checkpoint_prefix: str = "anima:checkpoint",
    checkpoint_blob_prefix: str = "anima:checkpoint_blob",
    checkpoint_write_prefix: str = "anima:checkpoint_write",
) -> AsyncIterator[AsyncRedisSaver]:
    """创建并管理 LangGraph Redis Checkpointer 生命周期。"""
    ttl_minutes = max(1, math.ceil(ttl_seconds / 60))
    async with AsyncRedisSaver.from_conn_string(
        redis_url,
        ttl={
            "default_ttl": ttl_minutes,
            "refresh_on_read": refresh_on_read,
        },
        checkpoint_prefix=checkpoint_prefix,
        checkpoint_blob_prefix=checkpoint_blob_prefix,
        checkpoint_write_prefix=checkpoint_write_prefix,
    ) as checkpointer:
        yield checkpointer
