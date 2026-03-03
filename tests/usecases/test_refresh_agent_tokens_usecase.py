from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from src.application.usecases.agent.refresh_agent_tokens import RefreshAgentTokensUseCase
from src.core.exceptions import AuthenticationFailedException
from src.domain.session.entities import Session


class InMemorySessionRepository:
    """Session 仓储测试替身。"""

    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._sessions: dict[str, Session] = {}

    async def get(self, *, session_id: str) -> Session | None:
        """按 ID 获取 Session。"""
        return self._sessions.get(session_id)

    async def create(
        self,
        *,
        session_id: str,
        max_agents_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建 Session 并返回实体。"""
        now = datetime.now(timezone.utc)
        created = Session(
            session_id=session_id,
            description=description,
            max_agents_limit=max_agents_limit,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = created
        return created

    async def delete(self, *, session_id: str) -> None:
        """删除 Session。"""
        self._sessions.pop(session_id, None)


class InMemoryProfileRepository:
    """画像仓储测试替身。"""

    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._profiles: dict[tuple[str, str], str] = {}

    async def save(
        self,
        *,
        session_id: str,
        agent_id: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """保存画像。"""
        _ = ttl_seconds
        self._profiles[(session_id, agent_id)] = profile_json

    async def get(self, *, session_id: str, agent_id: str) -> str | None:
        """读取画像。"""
        return self._profiles.get((session_id, agent_id))

    async def delete(self, *, session_id: str, agent_id: str) -> None:
        """删除画像。"""
        self._profiles.pop((session_id, agent_id), None)

    async def claim_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> bool:
        """占位实现。"""
        _ = (session_id, agent_id, display_name)
        return True

    async def release_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> None:
        """占位实现。"""
        _ = (session_id, agent_id, display_name)


class InMemoryAuthStateRepository:
    """鉴权状态仓储测试替身。"""

    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._token_versions: dict[tuple[str, str], int] = {}
        self._refresh_tokens: dict[tuple[str, str], set[str]] = {}

    async def ensure_token_version(
        self,
        *,
        session_id: str,
        agent_id: str,
        initial_version: int = 1,
    ) -> int:
        """确保 token_version 存在并返回当前值。"""
        key = (session_id, agent_id)
        current = self._token_versions.get(key)
        if current is None:
            self._token_versions[key] = initial_version
            return initial_version
        return current

    async def get_token_version(self, *, session_id: str, agent_id: str) -> int | None:
        """读取 token_version。"""
        return self._token_versions.get((session_id, agent_id))

    async def bump_token_version(self, *, session_id: str, agent_id: str) -> int:
        """提升 token_version。"""
        key = (session_id, agent_id)
        next_value = self._token_versions.get(key, 0) + 1
        self._token_versions[key] = next_value
        return next_value

    async def store_refresh_jti(
        self,
        *,
        session_id: str,
        agent_id: str,
        refresh_jti: str,
        ttl_seconds: int,
    ) -> None:
        """存储 refresh_jti。"""
        _ = ttl_seconds
        key = (session_id, agent_id)
        existing = self._refresh_tokens.setdefault(key, set())
        existing.add(refresh_jti)

    async def consume_refresh_jti(
        self,
        *,
        session_id: str,
        agent_id: str,
        refresh_jti: str,
    ) -> bool:
        """消费 refresh_jti。"""
        key = (session_id, agent_id)
        existing = self._refresh_tokens.setdefault(key, set())
        if refresh_jti not in existing:
            return False
        existing.remove(refresh_jti)
        return True

    async def revoke_all_refresh_jti(self, *, session_id: str, agent_id: str) -> None:
        """撤销全部 refresh_jti。"""
        self._refresh_tokens[(session_id, agent_id)] = set()


@dataclass(slots=True)
class FakeTokenClaims:
    """Token 解析结果测试载体。"""

    token_type: str
    session_id: str
    agent_id: str
    token_version: int
    expires_at: int
    refresh_jti: str | None = None


class FakeTokenService:
    """Token 服务测试替身。"""

    access_token_ttl_seconds = 900
    refresh_token_ttl_seconds = 604800

    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._claims_by_token: dict[str, FakeTokenClaims] = {}
        self._refresh_counter = 0

    def bind_token(self, *, token: str, claims: FakeTokenClaims) -> None:
        """为测试 token 绑定解析结果。"""
        self._claims_by_token[token] = claims

    async def parse_token(self, *, token: str) -> FakeTokenClaims:
        """解析 token。"""
        claims = self._claims_by_token.get(token)
        if claims is None:
            raise AuthenticationFailedException("invalid token")
        return claims

    async def issue_access_token(
        self,
        *,
        session_id: str,
        agent_id: str,
        token_version: int,
    ) -> str:
        """签发 access token。"""
        return f"access::{session_id}::{agent_id}::{token_version}"

    async def issue_refresh_token(
        self,
        *,
        session_id: str,
        agent_id: str,
        token_version: int,
        refresh_jti: str,
    ) -> str:
        """签发 refresh token。"""
        _ = refresh_jti
        self._refresh_counter += 1
        return f"refresh::{session_id}::{agent_id}::{token_version}::{self._refresh_counter}"

    async def generate_refresh_jti(self) -> str:
        """生成 refresh_jti。"""
        self._refresh_counter += 1
        return f"jti_{self._refresh_counter}"


@pytest.mark.asyncio
async def test_refresh_agent_tokens_usecase_rotates_tokens() -> None:
    """验证刷新成功时会消费旧 refresh 并返回新 token 对。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(session_id="session_demo", description=None, max_agents_limit=10)
    profile_repo = InMemoryProfileRepository()
    await profile_repo.save(
        session_id="session_demo",
        agent_id="agent_1",
        profile_json='{"name":"Alice","display_name":"Alice#12345","profile":"intro"}',
    )
    auth_repo = InMemoryAuthStateRepository()
    await auth_repo.ensure_token_version(session_id="session_demo", agent_id="agent_1")
    await auth_repo.store_refresh_jti(
        session_id="session_demo",
        agent_id="agent_1",
        refresh_jti="jti_old",
        ttl_seconds=604800,
    )
    token_service = FakeTokenService()
    token_service.bind_token(
        token="refresh_old_token",
        claims=FakeTokenClaims(
            token_type="refresh",
            session_id="session_demo",
            agent_id="agent_1",
            token_version=1,
            expires_at=9999999999,
            refresh_jti="jti_old",
        ),
    )
    usecase = RefreshAgentTokensUseCase(session_repo, profile_repo, auth_repo, token_service)

    result = await usecase.execute(
        session_id="session_demo",
        agent_id="agent_1",
        refresh_token="refresh_old_token",
    )

    assert result.token_type == "Bearer"
    assert result.access_token.startswith("access::session_demo::agent_1::1")
    assert result.refresh_token.startswith("refresh::session_demo::agent_1::1")
    assert result.access_token_expires_in == 900
    assert result.refresh_token_expires_in == 604800


@pytest.mark.asyncio
async def test_refresh_agent_tokens_usecase_revokes_all_when_replay_detected() -> None:
    """验证 refresh_jti 已消费时会触发重放保护并拒绝请求。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(session_id="session_demo", description=None, max_agents_limit=10)
    profile_repo = InMemoryProfileRepository()
    await profile_repo.save(
        session_id="session_demo",
        agent_id="agent_1",
        profile_json='{"name":"Alice","display_name":"Alice#12345","profile":"intro"}',
    )
    auth_repo = InMemoryAuthStateRepository()
    await auth_repo.ensure_token_version(session_id="session_demo", agent_id="agent_1")
    token_service = FakeTokenService()
    token_service.bind_token(
        token="refresh_replay_token",
        claims=FakeTokenClaims(
            token_type="refresh",
            session_id="session_demo",
            agent_id="agent_1",
            token_version=1,
            expires_at=9999999999,
            refresh_jti="already_used_jti",
        ),
    )
    usecase = RefreshAgentTokensUseCase(session_repo, profile_repo, auth_repo, token_service)

    with pytest.raises(AuthenticationFailedException):
        await usecase.execute(
            session_id="session_demo",
            agent_id="agent_1",
            refresh_token="refresh_replay_token",
        )

    assert await auth_repo.get_token_version(session_id="session_demo", agent_id="agent_1") == 2
