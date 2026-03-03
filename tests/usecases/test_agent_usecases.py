from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.application.dto.agent import AgentLifecycleResult
from src.application.usecases.agent.get_agent import GetAgentUseCase
from src.application.usecases.agent.patch_agent import PatchAgentUseCase
from src.application.usecases.agent.register_agent import RegisterAgentUseCase
from src.application.usecases.agent.unregister_agent import UnregisterAgentUseCase
from src.core.exceptions import (
    AgentNotFoundException,
    QuotaExceededException,
    SessionNotFoundException,
)
from src.domain.session.entities import Session


class InMemorySessionRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._sessions: dict[str, Session] = {}

    async def get(self, *, session_id: str) -> Session | None:
        """读取并返回 Session。"""
        return self._sessions.get(session_id)

    async def create(
        self,
        *,
        session_id: str,
        name: str | None = None,
        max_agents_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建并返回 Session。"""
        now = datetime.now(timezone.utc)
        created = Session(
            session_id=session_id,
            name=name or session_id,
            description=description,
            max_agents_limit=max_agents_limit,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = created
        return created

    async def update_quota(self, *, session_id: str, max_agents_limit: int) -> None:
        """更新 Session 配额。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return
        existing.max_agents_limit = max_agents_limit

    async def delete(self, *, session_id: str) -> None:
        """删除 Session。"""
        self._sessions.pop(session_id, None)


class InMemoryPresenceRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._active: dict[str, set[str]] = {}
        self._heartbeat: dict[tuple[str, str], int] = {}

    async def is_active(self, *, session_id: str, agent_id: str) -> bool:
        """判断实体是否在线。"""
        return agent_id in self._active.get(session_id, set())

    async def count_active(self, *, session_id: str) -> int:
        """统计在线实体数量。"""
        return len(self._active.get(session_id, set()))

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出在线实体。"""
        return sorted(self._active.get(session_id, set()))

    async def activate(self, *, session_id: str, agent_id: str) -> None:
        """激活实体在线状态。"""
        active = self._active.setdefault(session_id, set())
        active.add(agent_id)

    async def deactivate(self, *, session_id: str, agent_id: str) -> None:
        """取消实体在线状态。"""
        active = self._active.setdefault(session_id, set())
        active.discard(agent_id)

    async def touch_heartbeat(
        self,
        *,
        session_id: str,
        agent_id: str,
        ttl_seconds: int,
    ) -> None:
        """刷新心跳 TTL。"""
        self._heartbeat[(session_id, agent_id)] = ttl_seconds

    async def clear_heartbeat(self, *, session_id: str, agent_id: str) -> None:
        """清理心跳键。"""
        self._heartbeat.pop((session_id, agent_id), None)


class InMemoryProfileRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._profiles: dict[tuple[str, str], str] = {}
        self._display_name_index: dict[tuple[str, str], str] = {}

    async def save(
        self,
        *,
        session_id: str,
        agent_id: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """保存实体画像。"""
        _ = ttl_seconds
        self._profiles[(session_id, agent_id)] = profile_json

    async def get(self, *, session_id: str, agent_id: str) -> str | None:
        """读取实体画像。"""
        return self._profiles.get((session_id, agent_id))

    async def delete(self, *, session_id: str, agent_id: str) -> None:
        """删除实体画像。"""
        self._profiles.pop((session_id, agent_id), None)

    async def claim_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> bool:
        """尝试占用展示名。"""
        key = (session_id, display_name)
        current = self._display_name_index.get(key)
        if current is None:
            self._display_name_index[key] = agent_id
            return True
        return current == agent_id

    async def release_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> None:
        """释放展示名占用。"""
        key = (session_id, display_name)
        if self._display_name_index.get(key) != agent_id:
            return
        self._display_name_index.pop(key, None)


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


class FakeAgentTokenService:
    """Token 服务测试替身。"""

    access_token_ttl_seconds = 900
    refresh_token_ttl_seconds = 604800
    _refresh_counter = 0

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
        return f"refresh::{session_id}::{agent_id}::{token_version}::{refresh_jti}"

    async def generate_refresh_jti(self) -> str:
        """生成 refresh_jti。"""
        self._refresh_counter += 1
        return f"jti_{self._refresh_counter}"


@pytest.mark.asyncio
async def test_register_agent_usecase_registers_presence_and_profile() -> None:
    """验证注册成功时会写入在线状态与画像缓存。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    auth_repo = InMemoryAuthStateRepository()
    token_service = FakeAgentTokenService()
    usecase = RegisterAgentUseCase(session_repo, presence_repo, profile_repo, auth_repo, token_service)

    result = await usecase.execute(
        session_id="session_demo",
        name="Alice",
        profile="我是一个观察者",
    )

    assert isinstance(result, AgentLifecycleResult)
    assert result.session_id == "session_demo"
    assert result.agent_id
    assert result.name == "Alice"
    assert result.display_name is not None
    assert result.display_name.startswith("Alice#")
    assert len(result.display_name.split("#", maxsplit=1)[1]) == 5
    assert result.display_name.split("#", maxsplit=1)[1].isdigit()
    assert result.active is True
    assert result.token_type == "Bearer"
    assert result.access_token is not None
    assert result.access_token.startswith("access::")
    assert result.refresh_token is not None
    assert result.refresh_token.startswith("refresh::")
    assert result.access_token_expires_in == 900
    assert result.refresh_token_expires_in == 604800
    stored = await profile_repo.get(session_id="session_demo", agent_id=result.agent_id)
    assert stored is not None
    assert json.loads(stored) == {
        "name": "Alice",
        "display_name": result.display_name,
        "profile": "我是一个观察者",
    }
    assert await presence_repo.is_active(session_id="session_demo", agent_id=result.agent_id) is True


@pytest.mark.asyncio
async def test_register_agent_usecase_raises_when_quota_exceeded() -> None:
    """验证达到配额时会抛出限制异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=1,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    await presence_repo.activate(session_id="session_demo", agent_id="existing")
    usecase = RegisterAgentUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeAgentTokenService(),
    )

    with pytest.raises(QuotaExceededException):
        await usecase.execute(
            session_id="session_demo",
            name="Bob",
            profile="new",
        )


@pytest.mark.asyncio
async def test_register_agent_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    usecase = RegisterAgentUseCase(
        InMemorySessionRepository(),
        InMemoryPresenceRepository(),
        InMemoryProfileRepository(),
        InMemoryAuthStateRepository(),
        FakeAgentTokenService(),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_missing",
            name="Ghost",
            profile="x",
        )


@pytest.mark.asyncio
async def test_get_agent_usecase_returns_agent_detail() -> None:
    """验证可读取 Agent 信息。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    register_usecase = RegisterAgentUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeAgentTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        profile="hello",
    )

    usecase = GetAgentUseCase(session_repo, presence_repo, profile_repo)
    result = await usecase.execute(session_id="session_demo", agent_id=registered.agent_id)

    assert result.agent_id == registered.agent_id
    assert result.name == "Alice"
    assert result.profile == "hello"
    assert result.active is True


@pytest.mark.asyncio
async def test_patch_agent_usecase_updates_name_and_display_name() -> None:
    """验证可更新昵称并重算展示名。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    register_usecase = RegisterAgentUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeAgentTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        profile="hello",
    )

    usecase = PatchAgentUseCase(session_repo, presence_repo, profile_repo)
    result = await usecase.execute(
        session_id="session_demo",
        agent_id=registered.agent_id,
        name="AliceNew",
        profile=None,
    )

    assert result.name == "AliceNew"
    assert result.profile == "hello"
    assert result.display_name is not None
    assert result.display_name.startswith("AliceNew#")


@pytest.mark.asyncio
async def test_patch_agent_usecase_updates_profile_without_changing_display_name() -> None:
    """验证仅修改 profile 时保留原 display_name。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    register_usecase = RegisterAgentUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeAgentTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        profile="old_profile",
    )

    usecase = PatchAgentUseCase(session_repo, presence_repo, profile_repo)
    result = await usecase.execute(
        session_id="session_demo",
        agent_id=registered.agent_id,
        name=None,
        profile="new_profile",
    )

    assert result.name == "Alice"
    assert result.profile == "new_profile"
    assert result.display_name == registered.display_name


@pytest.mark.asyncio
async def test_unregister_agent_usecase_removes_presence_and_profile() -> None:
    """验证卸载成功时会清理在线状态与画像缓存。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    auth_repo = InMemoryAuthStateRepository()
    register_usecase = RegisterAgentUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        auth_repo,
        FakeAgentTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        profile="router",
    )
    usecase = UnregisterAgentUseCase(session_repo, presence_repo, profile_repo, auth_repo)

    result = await usecase.execute(session_id="session_demo", agent_id=registered.agent_id)

    assert isinstance(result, AgentLifecycleResult)
    assert result.session_id == "session_demo"
    assert result.agent_id == registered.agent_id
    assert result.active is False
    assert await presence_repo.is_active(session_id="session_demo", agent_id=registered.agent_id) is False
    assert await profile_repo.get(session_id="session_demo", agent_id=registered.agent_id) is None
    assert await auth_repo.get_token_version(session_id="session_demo", agent_id=registered.agent_id) == 2


@pytest.mark.asyncio
async def test_unregister_agent_usecase_raises_when_agent_missing() -> None:
    """验证实体不存在时会抛出异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=2,
    )
    usecase = UnregisterAgentUseCase(
        session_repo,
        InMemoryPresenceRepository(),
        InMemoryProfileRepository(),
        InMemoryAuthStateRepository(),
    )

    with pytest.raises(AgentNotFoundException):
        await usecase.execute(session_id="session_demo", agent_id="agent_missing")


@pytest.mark.asyncio
async def test_unregister_agent_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    usecase = UnregisterAgentUseCase(
        InMemorySessionRepository(),
        InMemoryPresenceRepository(),
        InMemoryProfileRepository(),
        InMemoryAuthStateRepository(),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(session_id="session_missing", agent_id="agent_a")
