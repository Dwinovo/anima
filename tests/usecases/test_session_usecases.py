from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.get_session import GetSessionUseCase
from src.application.usecases.session.list_sessions import ListSessionsUseCase
from src.application.usecases.session.patch_session import PatchSessionUseCase
from src.core.exceptions import SessionNotFoundException
from src.domain.session.entities import Session


class InMemorySessionRepository:
    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._sessions: dict[str, Session] = {}

    async def get(self, *, session_id: str) -> Session | None:
        """执行 `get` 相关逻辑。"""
        return self._sessions.get(session_id)

    async def list(self) -> list[Session]:
        """列出符合条件的数据集合。"""
        return [self._sessions[key] for key in sorted(self._sessions.keys())]

    async def create(
        self,
        *,
        session_id: str,
        max_agents_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建资源并返回创建结果。"""
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

    async def update_quota(self, *, session_id: str, max_agents_limit: int) -> None:
        """更新目标资源的状态或字段。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return
        existing.max_agents_limit = max_agents_limit
        existing.updated_at = datetime.now(timezone.utc)

    async def delete(self, *, session_id: str) -> None:
        """删除指定资源。"""
        self._sessions.pop(session_id, None)

    async def update(
        self,
        *,
        session_id: str,
        description: str | None = None,
        max_agents_limit: int | None = None,
    ) -> Session | None:
        """更新指定 Session。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return None
        if description is not None:
            existing.description = description
        if max_agents_limit is not None:
            existing.max_agents_limit = max_agents_limit
        existing.updated_at = datetime.now(timezone.utc)
        return existing


@pytest.mark.asyncio
async def test_create_session_usecase_keeps_client_session_id() -> None:
    """验证创建 Session 时使用客户端传入的 session_id。"""
    repo = InMemorySessionRepository()
    usecase = CreateSessionUseCase(repo)

    created = await usecase.execute(
        session_id="session_alpha",
        description="social world",
        max_agents_limit=100,
    )

    assert created.session_id == "session_alpha"
    assert created.description == "social world"
    assert created.max_agents_limit == 100


@pytest.mark.asyncio
async def test_delete_session_usecase_deletes_existing_session() -> None:
    """验证该测试场景的预期行为。"""
    repo = InMemorySessionRepository()
    created = await repo.create(
        session_id="session_deadbeef",
        description=None,
        max_agents_limit=10,
    )
    usecase = DeleteSessionUseCase(repo)

    await usecase.execute(session_id=created.session_id)

    assert await repo.get(session_id=created.session_id) is None


@pytest.mark.asyncio
async def test_delete_session_usecase_raises_for_missing_session() -> None:
    """验证该测试场景的预期行为。"""
    repo = InMemorySessionRepository()
    usecase = DeleteSessionUseCase(repo)

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(session_id="session_missing")


@pytest.mark.asyncio
async def test_list_sessions_usecase_returns_basic_infos_from_postgres() -> None:
    """验证该测试场景的预期行为。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_alpha",
        description="alpha desc",
        max_agents_limit=100,
    )
    await session_repo.create(
        session_id="session_beta",
        description=None,
        max_agents_limit=50,
    )
    usecase = ListSessionsUseCase(session_repo)

    result = await usecase.execute()

    assert len(result) == 2
    assert result[0].session_id == "session_alpha"
    assert result[0].description == "alpha desc"
    assert result[0].max_agents_limit == 100
    assert result[1].session_id == "session_beta"
    assert result[1].description is None
    assert result[1].max_agents_limit == 50


@pytest.mark.asyncio
async def test_get_session_usecase_returns_existing_session() -> None:
    """验证可读取 Session 详情。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_alpha",
        description=None,
        max_agents_limit=100,
    )
    usecase = GetSessionUseCase(session_repo)

    result = await usecase.execute(session_id="session_alpha")

    assert result.session_id == "session_alpha"
    assert result.max_agents_limit == 100
    assert result.created_at is not None
    assert result.updated_at is not None


@pytest.mark.asyncio
async def test_patch_session_usecase_updates_partial_fields() -> None:
    """验证可对 Session 执行增量更新。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_alpha",
        description=None,
        max_agents_limit=100,
    )
    usecase = PatchSessionUseCase(session_repo)

    result = await usecase.execute(
        session_id="session_alpha",
        description="new desc",
        max_agents_limit=120,
    )

    assert result.session_id == "session_alpha"
    assert result.description == "new desc"
    assert result.max_agents_limit == 120


@pytest.mark.asyncio
async def test_patch_session_usecase_raises_for_missing_session() -> None:
    """验证 Session 不存在时 PATCH 会抛出异常。"""
    session_repo = InMemorySessionRepository()
    usecase = PatchSessionUseCase(session_repo)

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_missing",
            description="new_desc",
        )
