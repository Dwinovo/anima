from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.usecases.entity.maintain_presence import MaintainEntityPresenceUseCase
from src.core.exceptions import EntityNotFoundException, SessionNotFoundException
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
        name: str | None = None,
        max_entities_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建 Session 并返回实体。"""
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

    async def list(self) -> list[Session]:
        """列出全部 Session。"""
        return list(self._sessions.values())

    async def update_quota(self, *, session_id: str, max_entities_limit: int) -> None:
        """更新配额。"""
        _ = (session_id, max_entities_limit)

    async def update(
        self,
        *,
        session_id: str,
        name: str | None = None,
        description: str | None = None,
        max_entities_limit: int | None = None,
    ) -> Session | None:
        """更新 Session。"""
        _ = (name, description, max_entities_limit)
        return self._sessions.get(session_id)

    async def delete(self, *, session_id: str) -> None:
        """删除 Session。"""
        self._sessions.pop(session_id, None)


class InMemoryProfileRepository:
    """画像仓储测试替身。"""

    def __init__(self, existing_entity_ids: set[str] | None = None) -> None:
        """初始化对象并注入所需依赖。"""
        self._existing_entity_ids = existing_entity_ids or set()

    async def save(
        self,
        *,
        session_id: str,
        entity_id: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """保存画像。"""
        _ = (session_id, profile_json, ttl_seconds)
        self._existing_entity_ids.add(entity_id)

    async def get(self, *, session_id: str, entity_id: str) -> str | None:
        """读取画像。"""
        _ = session_id
        if entity_id in self._existing_entity_ids:
            return '{"name":"demo"}'
        return None

    async def delete(self, *, session_id: str, entity_id: str) -> None:
        """删除画像。"""
        _ = session_id
        self._existing_entity_ids.discard(entity_id)

    async def claim_display_name(
        self,
        *,
        session_id: str,
        entity_id: str,
        display_name: str,
    ) -> bool:
        """占位实现。"""
        _ = (session_id, entity_id, display_name)
        return False

    async def release_display_name(
        self,
        *,
        session_id: str,
        entity_id: str,
        display_name: str,
    ) -> None:
        """占位实现。"""
        _ = (session_id, entity_id, display_name)


class InMemoryPresenceRepository:
    """在线态仓储测试替身。"""

    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self.active_ids: set[str] = set()
        self.heartbeat: dict[str, int] = {}

    async def is_active(self, *, session_id: str, entity_id: str) -> bool:
        """判断是否在线。"""
        _ = session_id
        return entity_id in self.active_ids

    async def count_active(self, *, session_id: str) -> int:
        """统计在线数量。"""
        _ = session_id
        return len(self.active_ids)

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出在线实体。"""
        _ = session_id
        return sorted(self.active_ids)

    async def activate(self, *, session_id: str, entity_id: str) -> None:
        """标记在线。"""
        _ = session_id
        self.active_ids.add(entity_id)

    async def deactivate(self, *, session_id: str, entity_id: str) -> None:
        """标记离线。"""
        _ = session_id
        self.active_ids.discard(entity_id)

    async def touch_heartbeat(
        self,
        *,
        session_id: str,
        entity_id: str,
        ttl_seconds: int,
    ) -> None:
        """刷新心跳 TTL。"""
        _ = session_id
        self.heartbeat[entity_id] = ttl_seconds

    async def clear_heartbeat(self, *, session_id: str, entity_id: str) -> None:
        """清理心跳。"""
        _ = session_id
        self.heartbeat.pop(entity_id, None)


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


@pytest.mark.asyncio
async def test_maintain_presence_on_connect_marks_entity_online_and_sets_heartbeat() -> None:
    """验证建立连接后会激活在线态并写入心跳 TTL。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(session_id="session_demo", max_entities_limit=10, description=None)
    profile_repo = InMemoryProfileRepository(existing_entity_ids={"entity_1"})
    presence_repo = InMemoryPresenceRepository()
    auth_repo = InMemoryAuthStateRepository()
    usecase = MaintainEntityPresenceUseCase(session_repo, profile_repo, presence_repo, auth_repo)

    await usecase.on_connect(
        session_id="session_demo",
        entity_id="entity_1",
        heartbeat_ttl_seconds=180,
    )

    assert "entity_1" in presence_repo.active_ids
    assert presence_repo.heartbeat["entity_1"] == 180


@pytest.mark.asyncio
async def test_maintain_presence_on_connect_raises_when_session_missing() -> None:
    """验证会话不存在时抛异常。"""
    usecase = MaintainEntityPresenceUseCase(
        InMemorySessionRepository(),
        InMemoryProfileRepository(existing_entity_ids={"entity_1"}),
        InMemoryPresenceRepository(),
        InMemoryAuthStateRepository(),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.on_connect(
            session_id="session_missing",
            entity_id="entity_1",
            heartbeat_ttl_seconds=180,
        )


@pytest.mark.asyncio
async def test_maintain_presence_on_connect_raises_when_entity_missing() -> None:
    """验证 Entity 不存在时抛异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(session_id="session_demo", max_entities_limit=10, description=None)
    usecase = MaintainEntityPresenceUseCase(
        session_repo,
        InMemoryProfileRepository(existing_entity_ids=set()),
        InMemoryPresenceRepository(),
        InMemoryAuthStateRepository(),
    )

    with pytest.raises(EntityNotFoundException):
        await usecase.on_connect(
            session_id="session_demo",
            entity_id="entity_missing",
            heartbeat_ttl_seconds=180,
        )


@pytest.mark.asyncio
async def test_maintain_presence_on_disconnect_cleans_presence_and_heartbeat() -> None:
    """验证断开连接会清理在线态、心跳与 profile。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(session_id="session_demo", max_entities_limit=10, description=None)
    profile_repo = InMemoryProfileRepository(existing_entity_ids={"entity_1"})
    presence_repo = InMemoryPresenceRepository()
    auth_repo = InMemoryAuthStateRepository()
    await auth_repo.ensure_token_version(session_id="session_demo", entity_id="entity_1")
    usecase = MaintainEntityPresenceUseCase(session_repo, profile_repo, presence_repo, auth_repo)

    await usecase.on_connect(
        session_id="session_demo",
        entity_id="entity_1",
        heartbeat_ttl_seconds=180,
    )
    await usecase.on_disconnect(session_id="session_demo", entity_id="entity_1")

    assert "entity_1" not in presence_repo.active_ids
    assert "entity_1" not in presence_repo.heartbeat
    assert await profile_repo.get(session_id="session_demo", entity_id="entity_1") is None
    assert await auth_repo.get_token_version(session_id="session_demo", entity_id="entity_1") == 2
