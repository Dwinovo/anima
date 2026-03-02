# src/domain/agent/profile_repository.py
from __future__ import annotations

from typing import Protocol


class AgentProfileRepository(Protocol):
    async def save(
        self,
        *,
        session_id: str,
        uuid: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """保存指定实体的画像数据。"""
        ...

    async def get(self, *, session_id: str, uuid: str) -> str | None:
        """读取指定实体的画像数据。"""
        ...

    async def delete(self, *, session_id: str, uuid: str) -> None:
        """删除指定实体的画像数据。"""
        ...

    async def claim_display_name(
        self,
        *,
        session_id: str,
        uuid: str,
        display_name: str,
    ) -> bool:
        """尝试占用展示名，成功返回 ``True``。"""
        ...

    async def release_display_name(
        self,
        *,
        session_id: str,
        uuid: str,
        display_name: str,
    ) -> None:
        """释放指定实体占用的展示名。"""
        ...
