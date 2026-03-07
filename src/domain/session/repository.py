from __future__ import annotations

from typing import Protocol

from src.domain.session.actions import SessionAction
from src.domain.session.entities import Session


class SessionRepository(Protocol):
    async def list(self) -> list[Session]:
        """列出全部会话配置。"""
        ...

    async def get(self, *, session_id: str) -> Session | None:
        """按 session_id 查询会话配置。"""
        ...

    async def create(
        self,
        *,
        session_id: str,
        name: str,
        max_entities_limit: int,
        actions: tuple[SessionAction, ...],
        description: str | None = None,
    ) -> Session:
        """创建会话配置并返回领域实体。"""
        ...

    async def update_quota(
        self,
        *,
        session_id: str,
        max_entities_limit: int,
    ) -> None:
        """更新指定会话的配额上限。"""
        ...

    async def update(
        self,
        *,
        session_id: str,
        name: str | None = None,
        description: str | None = None,
        max_entities_limit: int | None = None,
        actions: tuple[SessionAction, ...] | None = None,
    ) -> Session | None:
        """更新指定会话配置。"""
        ...

    async def delete(self, *, session_id: str) -> None:
        """删除指定会话配置。"""
        ...
