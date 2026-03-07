from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.usecases.session.create_session import CreateSessionUseCase
from src.application.usecases.session.delete_session import DeleteSessionUseCase
from src.application.usecases.session.get_session import GetSessionUseCase
from src.application.usecases.session.list_sessions import ListSessionsUseCase
from src.application.usecases.session.patch_session import PatchSessionUseCase
from src.core.exceptions import SessionNotFoundException
from src.domain.session.actions import SessionAction, session_actions_from_payload
from src.domain.session.entities import Session


def build_default_actions() -> list[dict[str, object]]:
    """构造最小合法的 Session actions 配置。"""
    return [
        {
            "verb": "social.posted",
            "description": "post to board",
            "details_schema": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {
                        "type": "string",
                        "minLength": 1,
                    }
                },
                "additionalProperties": False,
            },
        }
    ]


def build_updated_actions() -> list[dict[str, object]]:
    """构造 PATCH 后的新动作配置。"""
    return [
        {
            "verb": "combat.attacked",
            "description": "attack another entity",
            "details_schema": {
                "type": "object",
                "required": ["damage"],
                "properties": {
                    "damage": {
                        "type": "integer",
                        "minimum": 1,
                    }
                },
                "additionalProperties": False,
            },
        }
    ]


def normalize_actions(
    actions: list[dict[str, object]] | tuple[SessionAction, ...] | None,
) -> tuple[SessionAction, ...]:
    """统一将测试输入动作转换为领域对象。"""
    if actions is None:
        return ()
    if actions and isinstance(actions[0], SessionAction):
        return actions
    return session_actions_from_payload(actions)


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
        name: str,
        max_entities_limit: int,
        description: str | None = None,
        actions: list[dict[str, object]] | None = None,
    ) -> Session:
        """创建资源并返回创建结果。"""
        now = datetime.now(timezone.utc)
        created = Session(
            session_id=session_id,
            name=name,
            description=description,
            max_entities_limit=max_entities_limit,
            actions=normalize_actions(actions),
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = created
        return created

    async def update_quota(self, *, session_id: str, max_entities_limit: int) -> None:
        """更新目标资源的状态或字段。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return
        existing.max_entities_limit = max_entities_limit
        existing.updated_at = datetime.now(timezone.utc)

    async def delete(self, *, session_id: str) -> None:
        """删除指定资源。"""
        self._sessions.pop(session_id, None)

    async def update(
        self,
        *,
        session_id: str,
        name: str | None = None,
        description: str | None = None,
        max_entities_limit: int | None = None,
        actions: list[dict[str, object]] | None = None,
    ) -> Session | None:
        """更新指定 Session。"""
        existing = self._sessions.get(session_id)
        if existing is None:
            return None
        if name is not None:
            existing.name = name
        if description is not None:
            existing.description = description
        if max_entities_limit is not None:
            existing.max_entities_limit = max_entities_limit
        if actions is not None:
            existing.actions = normalize_actions(actions)
        existing.updated_at = datetime.now(timezone.utc)
        return existing


@pytest.mark.asyncio
async def test_create_session_usecase_generates_server_side_uuid() -> None:
    """验证创建 Session 时由服务端生成 session_id。"""
    repo = InMemorySessionRepository()
    usecase = CreateSessionUseCase(repo)

    created = await usecase.execute(
        name="Alpha Session",
        description="social world",
        max_entities_limit=100,
        actions=build_default_actions(),
    )

    UUID(created.session_id)
    assert created.name == "Alpha Session"
    assert created.description == "social world"
    assert created.max_entities_limit == 100
    assert len(created.actions) == 1
    assert created.actions[0].verb == "social.posted"


@pytest.mark.asyncio
async def test_delete_session_usecase_deletes_existing_session() -> None:
    """验证该测试场景的预期行为。"""
    repo = InMemorySessionRepository()
    created = await repo.create(
        session_id="session_deadbeef",
        name="Deadbeef Session",
        description=None,
        max_entities_limit=10,
        actions=build_default_actions(),
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
        name="Alpha Session",
        description="alpha desc",
        max_entities_limit=100,
        actions=build_default_actions(),
    )
    await session_repo.create(
        session_id="session_beta",
        name="Beta Session",
        description=None,
        max_entities_limit=50,
        actions=build_default_actions(),
    )
    usecase = ListSessionsUseCase(session_repo)

    result = await usecase.execute()

    assert len(result) == 2
    assert result[0].session_id == "session_alpha"
    assert result[0].name == "Alpha Session"
    assert result[0].description == "alpha desc"
    assert result[0].max_entities_limit == 100
    assert result[1].session_id == "session_beta"
    assert result[1].name == "Beta Session"
    assert result[1].description is None
    assert result[1].max_entities_limit == 50


@pytest.mark.asyncio
async def test_get_session_usecase_returns_existing_session() -> None:
    """验证可读取 Session 详情。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_alpha",
        name="Alpha Session",
        description=None,
        max_entities_limit=100,
        actions=build_default_actions(),
    )
    usecase = GetSessionUseCase(session_repo)

    result = await usecase.execute(session_id="session_alpha")

    assert result.session_id == "session_alpha"
    assert result.name == "Alpha Session"
    assert result.max_entities_limit == 100
    assert len(result.actions) == 1
    assert result.actions[0].verb == "social.posted"
    assert result.created_at is not None
    assert result.updated_at is not None


@pytest.mark.asyncio
async def test_patch_session_usecase_updates_partial_fields() -> None:
    """验证可对 Session 执行增量更新。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_alpha",
        name="Alpha Session",
        description=None,
        max_entities_limit=100,
        actions=build_default_actions(),
    )
    usecase = PatchSessionUseCase(session_repo)

    result = await usecase.execute(
        session_id="session_alpha",
        name="Alpha Session V2",
        description="new desc",
        max_entities_limit=120,
        actions=build_updated_actions(),
    )

    assert result.session_id == "session_alpha"
    assert result.name == "Alpha Session V2"
    assert result.description == "new desc"
    assert result.max_entities_limit == 120
    assert len(result.actions) == 1
    assert result.actions[0].verb == "combat.attacked"


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
