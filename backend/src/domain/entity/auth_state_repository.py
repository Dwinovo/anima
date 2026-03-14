from __future__ import annotations

from typing import Protocol


class EntityAuthStateRepository(Protocol):
    """Entity 鉴权状态仓储协议。"""

    async def ensure_token_version(
        self,
        *,
        session_id: str,
        entity_id: str,
        initial_version: int = 1,
    ) -> int:
        """确保 token_version 存在并返回当前值。"""
        ...

    async def get_token_version(self, *, session_id: str, entity_id: str) -> int | None:
        """读取 token_version。"""
        ...

    async def bump_token_version(self, *, session_id: str, entity_id: str) -> int:
        """提升 token_version 并返回新值。"""
        ...

    async def store_refresh_jti(
        self,
        *,
        session_id: str,
        entity_id: str,
        refresh_jti: str,
        ttl_seconds: int,
    ) -> None:
        """存储 refresh_jti。"""
        ...

    async def consume_refresh_jti(
        self,
        *,
        session_id: str,
        entity_id: str,
        refresh_jti: str,
    ) -> bool:
        """消费 refresh_jti（单次生效）。"""
        ...

    async def revoke_all_refresh_jti(self, *, session_id: str, entity_id: str) -> None:
        """撤销指定 Entity 的全部 refresh_jti。"""
        ...
