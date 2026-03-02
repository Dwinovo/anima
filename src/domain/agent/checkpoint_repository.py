from __future__ import annotations

from typing import Protocol


class AgentCheckpointRepository(Protocol):
    """Agent 短期工作记忆（LangGraph checkpoint）仓储接口。"""

    async def load(self, *, session_id: str, uuid: str) -> list[str]:
        """读取指定 Agent 的短期记忆快照。"""
        ...

    async def save(
        self,
        *,
        session_id: str,
        uuid: str,
        snapshots: list[str],
        ttl_seconds: int,
    ) -> None:
        """写入指定 Agent 的短期记忆快照并设置 TTL。"""
        ...

    async def clear(self, *, session_id: str, uuid: str) -> None:
        """清空指定 Agent 的短期记忆快照。"""
        ...
