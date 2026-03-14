from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class TokenClaims:
    """Token 解析后的结构化声明。"""

    token_type: str
    session_id: str
    entity_id: str
    token_version: int
    expires_at: int
    refresh_jti: str | None = None


class EntityTokenService(Protocol):
    """Entity 令牌服务协议。"""

    access_token_ttl_seconds: int
    refresh_token_ttl_seconds: int

    async def issue_access_token(
        self,
        *,
        session_id: str,
        entity_id: str,
        token_version: int,
    ) -> str:
        """签发 access token。"""
        ...

    async def issue_refresh_token(
        self,
        *,
        session_id: str,
        entity_id: str,
        token_version: int,
        refresh_jti: str,
    ) -> str:
        """签发 refresh token。"""
        ...

    async def parse_token(self, *, token: str) -> TokenClaims:
        """解析并校验 token。"""
        ...

    async def generate_refresh_jti(self) -> str:
        """生成 refresh_jti。"""
        ...
