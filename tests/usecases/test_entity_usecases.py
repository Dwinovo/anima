from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.application.dto.entity import EntityLifecycleResult
from src.application.usecases.entity.get_entity import GetEntityUseCase
from src.application.usecases.entity.patch_entity import PatchEntityUseCase
from src.application.usecases.entity.register_entity import RegisterEntityUseCase
from src.application.usecases.entity.unregister_entity import UnregisterEntityUseCase
from src.core.exceptions import (
    EntityNotFoundException,
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
        max_entities_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建并返回 Session。"""
        now = datetime.now(timezone.utc)
        created = Session(
            session_id=session_id,
            name=name or session_id,
            description=description,
            max_entities_limit=max_entities_limit,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = created
        return created

    async def update_quota(self, *, session_id: str, max_entities_limit: int) -> None:
        """更新 Session 配额。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return
        existing.max_entities_limit = max_entities_limit

    async def delete(self, *, session_id: str) -> None:
        """删除 Session。"""
        self._sessions.pop(session_id, None)


class InMemoryPresenceRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._active: dict[str, set[str]] = {}
        self._heartbeat: dict[tuple[str, str], int] = {}

    async def is_active(self, *, session_id: str, entity_id: str) -> bool:
        """判断实体是否在线。"""
        return entity_id in self._active.get(session_id, set())

    async def count_active(self, *, session_id: str) -> int:
        """统计在线实体数量。"""
        return len(self._active.get(session_id, set()))

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出在线实体。"""
        return sorted(self._active.get(session_id, set()))

    async def activate(self, *, session_id: str, entity_id: str) -> None:
        """激活实体在线状态。"""
        active = self._active.setdefault(session_id, set())
        active.add(entity_id)

    async def deactivate(self, *, session_id: str, entity_id: str) -> None:
        """取消实体在线状态。"""
        active = self._active.setdefault(session_id, set())
        active.discard(entity_id)

    async def touch_heartbeat(
        self,
        *,
        session_id: str,
        entity_id: str,
        ttl_seconds: int,
    ) -> None:
        """刷新心跳 TTL。"""
        self._heartbeat[(session_id, entity_id)] = ttl_seconds

    async def clear_heartbeat(self, *, session_id: str, entity_id: str) -> None:
        """清理心跳键。"""
        self._heartbeat.pop((session_id, entity_id), None)


class InMemoryProfileRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._profiles: dict[tuple[str, str], str] = {}
        self._display_name_index: dict[tuple[str, str], str] = {}

    async def save(
        self,
        *,
        session_id: str,
        entity_id: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """保存实体画像。"""
        _ = ttl_seconds
        self._profiles[(session_id, entity_id)] = profile_json

    async def get(self, *, session_id: str, entity_id: str) -> str | None:
        """读取实体画像。"""
        return self._profiles.get((session_id, entity_id))

    async def delete(self, *, session_id: str, entity_id: str) -> None:
        """删除实体画像。"""
        self._profiles.pop((session_id, entity_id), None)

    async def claim_display_name(
        self,
        *,
        session_id: str,
        entity_id: str,
        display_name: str,
    ) -> bool:
        """尝试占用展示名。"""
        key = (session_id, display_name)
        current = self._display_name_index.get(key)
        if current is None:
            self._display_name_index[key] = entity_id
            return True
        return current == entity_id

    async def release_display_name(
        self,
        *,
        session_id: str,
        entity_id: str,
        display_name: str,
    ) -> None:
        """释放展示名占用。"""
        key = (session_id, display_name)
        if self._display_name_index.get(key) != entity_id:
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
        entity_id: str,
        initial_version: int = 1,
    ) -> int:
        """确保 token_version 存在并返回当前值。"""
        key = (session_id, entity_id)
        current = self._token_versions.get(key)
        if current is None:
            self._token_versions[key] = initial_version
            return initial_version
        return current

    async def get_token_version(self, *, session_id: str, entity_id: str) -> int | None:
        """读取 token_version。"""
        return self._token_versions.get((session_id, entity_id))

    async def bump_token_version(self, *, session_id: str, entity_id: str) -> int:
        """提升 token_version。"""
        key = (session_id, entity_id)
        next_value = self._token_versions.get(key, 0) + 1
        self._token_versions[key] = next_value
        return next_value

    async def store_refresh_jti(
        self,
        *,
        session_id: str,
        entity_id: str,
        refresh_jti: str,
        ttl_seconds: int,
    ) -> None:
        """存储 refresh_jti。"""
        _ = ttl_seconds
        key = (session_id, entity_id)
        existing = self._refresh_tokens.setdefault(key, set())
        existing.add(refresh_jti)

    async def consume_refresh_jti(
        self,
        *,
        session_id: str,
        entity_id: str,
        refresh_jti: str,
    ) -> bool:
        """消费 refresh_jti。"""
        key = (session_id, entity_id)
        existing = self._refresh_tokens.setdefault(key, set())
        if refresh_jti not in existing:
            return False
        existing.remove(refresh_jti)
        return True

    async def revoke_all_refresh_jti(self, *, session_id: str, entity_id: str) -> None:
        """撤销全部 refresh_jti。"""
        self._refresh_tokens[(session_id, entity_id)] = set()


class FakeEntityTokenService:
    """Token 服务测试替身。"""

    access_token_ttl_seconds = 900
    refresh_token_ttl_seconds = 604800
    _refresh_counter = 0

    async def issue_access_token(
        self,
        *,
        session_id: str,
        entity_id: str,
        token_version: int,
    ) -> str:
        """签发 access token。"""
        return f"access::{session_id}::{entity_id}::{token_version}"

    async def issue_refresh_token(
        self,
        *,
        session_id: str,
        entity_id: str,
        token_version: int,
        refresh_jti: str,
    ) -> str:
        """签发 refresh token。"""
        return f"refresh::{session_id}::{entity_id}::{token_version}::{refresh_jti}"

    async def generate_refresh_jti(self) -> str:
        """生成 refresh_jti。"""
        self._refresh_counter += 1
        return f"jti_{self._refresh_counter}"


@pytest.mark.asyncio
async def test_register_entity_usecase_registers_presence_and_runtime_payload() -> None:
    """验证注册成功时会写入在线状态与运行态缓存。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    auth_repo = InMemoryAuthStateRepository()
    token_service = FakeEntityTokenService()
    usecase = RegisterEntityUseCase(session_repo, presence_repo, profile_repo, auth_repo, token_service)

    result = await usecase.execute(
        session_id="session_demo",
        name="Alice",
        source="minecraft",
    )

    assert isinstance(result, EntityLifecycleResult)
    assert result.session_id == "session_demo"
    assert result.entity_id
    assert result.name == "Alice"
    assert result.source == "minecraft"
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
    stored = await profile_repo.get(session_id="session_demo", entity_id=result.entity_id)
    assert stored is not None
    assert json.loads(stored) == {
        "name": "Alice",
        "display_name": result.display_name,
        "source": "minecraft",
    }
    assert await presence_repo.is_active(session_id="session_demo", entity_id=result.entity_id) is True


@pytest.mark.asyncio
async def test_register_entity_usecase_raises_when_quota_exceeded() -> None:
    """验证达到配额时会抛出限制异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=1,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    await presence_repo.activate(session_id="session_demo", entity_id="existing")
    usecase = RegisterEntityUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeEntityTokenService(),
    )

    with pytest.raises(QuotaExceededException):
        await usecase.execute(
            session_id="session_demo",
            name="Bob",
            source="minecraft",
        )


@pytest.mark.asyncio
async def test_register_entity_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    usecase = RegisterEntityUseCase(
        InMemorySessionRepository(),
        InMemoryPresenceRepository(),
        InMemoryProfileRepository(),
        InMemoryAuthStateRepository(),
        FakeEntityTokenService(),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_missing",
            name="Ghost",
            source="minecraft",
        )


@pytest.mark.asyncio
async def test_get_entity_usecase_returns_entity_detail() -> None:
    """验证可读取 Entity 信息。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    register_usecase = RegisterEntityUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeEntityTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        source="minecraft",
    )

    usecase = GetEntityUseCase(session_repo, presence_repo, profile_repo)
    result = await usecase.execute(session_id="session_demo", entity_id=registered.entity_id)

    assert result.entity_id == registered.entity_id
    assert result.name == "Alice"
    assert result.source == "minecraft"
    assert result.active is True


@pytest.mark.asyncio
async def test_patch_entity_usecase_updates_name_and_display_name() -> None:
    """验证可更新昵称并重算展示名。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    register_usecase = RegisterEntityUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeEntityTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        source="minecraft",
    )

    usecase = PatchEntityUseCase(session_repo, presence_repo, profile_repo)
    result = await usecase.execute(
        session_id="session_demo",
        entity_id=registered.entity_id,
        name="AliceNew",
    )

    assert result.name == "AliceNew"
    assert result.source == "minecraft"
    assert result.display_name is not None
    assert result.display_name.startswith("AliceNew#")


@pytest.mark.asyncio
async def test_patch_entity_usecase_keeps_source_when_updating_name() -> None:
    """验证仅更新 name 时保留 source。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    register_usecase = RegisterEntityUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        InMemoryAuthStateRepository(),
        FakeEntityTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        source="minecraft",
    )

    usecase = PatchEntityUseCase(session_repo, presence_repo, profile_repo)
    result = await usecase.execute(
        session_id="session_demo",
        entity_id=registered.entity_id,
        name="AliceV2",
    )

    assert result.name == "AliceV2"
    assert result.source == "minecraft"
    assert result.display_name != registered.display_name


@pytest.mark.asyncio
async def test_unregister_entity_usecase_removes_presence_and_profile() -> None:
    """验证卸载成功时会清理在线状态与画像缓存。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=2,
    )
    presence_repo = InMemoryPresenceRepository()
    profile_repo = InMemoryProfileRepository()
    auth_repo = InMemoryAuthStateRepository()
    register_usecase = RegisterEntityUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        auth_repo,
        FakeEntityTokenService(),
    )
    registered = await register_usecase.execute(
        session_id="session_demo",
        name="Alice",
        source="minecraft",
    )
    usecase = UnregisterEntityUseCase(session_repo, presence_repo, profile_repo, auth_repo)

    result = await usecase.execute(session_id="session_demo", entity_id=registered.entity_id)

    assert isinstance(result, EntityLifecycleResult)
    assert result.session_id == "session_demo"
    assert result.entity_id == registered.entity_id
    assert result.active is False
    assert await presence_repo.is_active(session_id="session_demo", entity_id=registered.entity_id) is False
    assert await profile_repo.get(session_id="session_demo", entity_id=registered.entity_id) is None
    assert await auth_repo.get_token_version(session_id="session_demo", entity_id=registered.entity_id) == 2


@pytest.mark.asyncio
async def test_unregister_entity_usecase_raises_when_entity_missing() -> None:
    """验证实体不存在时会抛出异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_entities_limit=2,
    )
    usecase = UnregisterEntityUseCase(
        session_repo,
        InMemoryPresenceRepository(),
        InMemoryProfileRepository(),
        InMemoryAuthStateRepository(),
    )

    with pytest.raises(EntityNotFoundException):
        await usecase.execute(session_id="session_demo", entity_id="entity_missing")


@pytest.mark.asyncio
async def test_unregister_entity_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    usecase = UnregisterEntityUseCase(
        InMemorySessionRepository(),
        InMemoryPresenceRepository(),
        InMemoryProfileRepository(),
        InMemoryAuthStateRepository(),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(session_id="session_missing", entity_id="entity_a")
