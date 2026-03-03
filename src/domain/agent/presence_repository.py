# src/domain/agent/presence_repository.py
from __future__ import annotations

from typing import Protocol


class AgentPresenceRepository(Protocol):
    async def is_active(self, *, session_id: str, agent_id: str) -> bool:
        """判断指定实体当前是否在线。"""
        ...

    async def count_active(self, *, session_id: str) -> int:
        """统计指定会话下的在线实体数量。"""
        ...

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出指定会话下所有在线实体 UUID。"""
        ...

    async def activate(self, *, session_id: str, agent_id: str) -> None:
        """将指定实体标记为在线状态。"""
        ...

    async def deactivate(self, *, session_id: str, agent_id: str) -> None:
        """将指定实体标记为离线状态。"""
        ...
