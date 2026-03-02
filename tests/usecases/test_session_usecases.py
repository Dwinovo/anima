from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.list_sessions import (
    ListSessionsUseCase,
)
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
        default_llm: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Session:
        """创建资源并返回创建结果。"""
        created = Session(
            session_id=session_id,
            name=name or session_id,
            description=description,
            max_agents_limit=max_agents_limit,
            default_llm=default_llm,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
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


@pytest.mark.asyncio
async def test_create_session_usecase_generates_session_id_and_uses_default_llm() -> None:
    """验证该测试场景的预期行为。"""
    repo = InMemorySessionRepository()
    usecase = CreateSessionUseCase(repo, default_llm_model="gpt-4o")

    created = await usecase.execute(
        name="Cyber City Alpha",
        description="social world",
        max_agents_limit=100,
        default_llm=None,
    )

    assert created.session_id.startswith("session_")
    assert created.default_llm == "gpt-4o"
    assert created.name == "Cyber City Alpha"


@pytest.mark.asyncio
async def test_create_session_usecase_keeps_explicit_default_llm() -> None:
    """验证该测试场景的预期行为。"""
    repo = InMemorySessionRepository()
    usecase = CreateSessionUseCase(repo, default_llm_model="gpt-4o")

    created = await usecase.execute(
        name="Edge Realm",
        description=None,
        max_agents_limit=64,
        default_llm="gpt-4.1-mini",
    )

    assert created.default_llm == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_delete_session_usecase_deletes_existing_session() -> None:
    """验证该测试场景的预期行为。"""
    repo = InMemorySessionRepository()
    created = await repo.create(
        session_id="session_deadbeef",
        name="To Remove",
        description=None,
        max_agents_limit=10,
        default_llm="gpt-4o",
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
        name="Alpha",
        description="alpha desc",
        max_agents_limit=100,
        default_llm="gpt-4o",
    )
    await session_repo.create(
        session_id="session_beta",
        name="Beta",
        description=None,
        max_agents_limit=50,
        default_llm="gpt-4.1-mini",
    )
    usecase = ListSessionsUseCase(session_repo)

    result = await usecase.execute()

    assert len(result) == 2
    assert result[0].session_id == "session_alpha"
    assert result[0].name == "Alpha"
    assert result[0].max_agents_limit == 100
    assert result[1].session_id == "session_beta"
    assert result[1].name == "Beta"
    assert result[1].max_agents_limit == 50
