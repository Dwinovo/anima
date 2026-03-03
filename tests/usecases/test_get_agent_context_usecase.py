from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from src.application.usecases.agent.get_agent_context import GetAgentContextUseCase
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
from src.domain.session.entities import Session


class InMemorySessionRepository:
    """Session 仓储测试替身。"""

    def __init__(self) -> None:
        """初始化对象并注入所需依赖。"""
        self._sessions: dict[str, Session] = {}

    async def get(self, *, session_id: str) -> Session | None:
        """读取 Session。"""
        return self._sessions.get(session_id)

    async def create(
        self,
        *,
        session_id: str,
        name: str | None = None,
        max_agents_limit: int,
        description: str | None = None,
    ) -> Session:
        """创建 Session。"""
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

    async def list(self) -> list[Session]:
        """列出全部 Session。"""
        return list(self._sessions.values())

    async def update_quota(self, *, session_id: str, max_agents_limit: int) -> None:
        """更新 Session 配额。"""
        _ = max_agents_limit
        if session_id not in self._sessions:
            return

    async def update(
        self,
        *,
        session_id: str,
        name: str | None = None,
        description: str | None = None,
        max_agents_limit: int | None = None,
    ) -> Session | None:
        """更新 Session。"""
        _ = (name, description)
        _ = max_agents_limit
        return self._sessions.get(session_id)

    async def delete(self, *, session_id: str) -> None:
        """删除 Session。"""
        self._sessions.pop(session_id, None)


class InMemoryPresenceRepository:
    """在线态仓储测试替身。"""

    def __init__(self, active_ids: set[str] | None = None) -> None:
        """初始化对象并注入所需依赖。"""
        self._active_ids = active_ids or set()

    async def is_active(self, *, session_id: str, agent_id: str) -> bool:
        """判断 Agent 是否在线。"""
        _ = session_id
        return agent_id in self._active_ids

    async def count_active(self, *, session_id: str) -> int:
        """返回在线总数。"""
        _ = session_id
        return len(self._active_ids)

    async def list_active(self, *, session_id: str) -> list[str]:
        """列出在线 Agent。"""
        _ = session_id
        return sorted(self._active_ids)

    async def activate(self, *, session_id: str, agent_id: str) -> None:
        """激活在线态。"""
        _ = session_id
        self._active_ids.add(agent_id)

    async def deactivate(self, *, session_id: str, agent_id: str) -> None:
        """取消在线态。"""
        _ = session_id
        self._active_ids.discard(agent_id)


class InMemoryProfileRepository:
    """画像仓储测试替身。"""

    def __init__(self, existing_ids: set[str] | None = None) -> None:
        """初始化对象并注入所需依赖。"""
        self._existing_ids = existing_ids or set()

    async def save(
        self,
        *,
        session_id: str,
        agent_id: str,
        profile_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """写入画像。"""
        _ = (session_id, profile_json, ttl_seconds)
        self._existing_ids.add(agent_id)

    async def get(self, *, session_id: str, agent_id: str) -> str | None:
        """读取画像。"""
        _ = session_id
        if agent_id in self._existing_ids:
            return '{"name":"demo"}'
        return None

    async def delete(self, *, session_id: str, agent_id: str) -> None:
        """删除画像。"""
        _ = session_id
        self._existing_ids.discard(agent_id)

    async def claim_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> bool:
        """占位实现。"""
        _ = (session_id, agent_id, display_name)
        return False

    async def release_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        display_name: str,
    ) -> None:
        """占位实现。"""
        _ = (session_id, agent_id, display_name)


class InMemoryPayloadRepository:
    """事件载荷仓储测试替身。"""

    def __init__(self, payloads: dict[str, dict[str, Any]]) -> None:
        """初始化对象并注入所需依赖。"""
        self._payloads = payloads

    async def put(self, *, event_id: str, doc: dict[str, Any]) -> None:
        """写入事件载荷。"""
        self._payloads[event_id] = doc

    async def get(self, *, event_id: str) -> dict[str, Any] | None:
        """读取单条载荷。"""
        return self._payloads.get(event_id)

    async def mget(self, *, event_ids: list[str]) -> dict[str, dict[str, Any]]:
        """批量读取载荷。"""
        return {
            event_id: self._payloads[event_id]
            for event_id in event_ids
            if event_id in self._payloads
        }


class InMemoryGraphRepository:
    """图谱仓储测试替身。"""

    def __init__(self, event_ids: list[str]) -> None:
        """初始化对象并注入所需依赖。"""
        self._event_ids = event_ids

    async def upsert_event(
        self,
        *,
        session_id: str,
        event_id: str,
        world_time: int,
        verb: str,
        subject_uuid: str,
        target_ref: str,
        is_social: bool,
    ) -> None:
        """占位实现。"""
        _ = (session_id, event_id, world_time, verb, subject_uuid, target_ref, is_social)

    async def list_recent_event_ids(
        self,
        *,
        session_id: str,
        limit: int,
        before_world_time: int | None = None,
        before_event_id: str | None = None,
    ) -> list[str]:
        """返回预置事件 ID。"""
        _ = (session_id, before_world_time, before_event_id)
        return list(self._event_ids[:limit])


@pytest.mark.asyncio
async def test_get_agent_context_usecase_returns_views_payload() -> None:
    """验证上下文分流为 views 六视图结构。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    presence_repo = InMemoryPresenceRepository(active_ids={"agent_me"})
    profile_repo = InMemoryProfileRepository(existing_ids={"agent_me"})
    payload_repo = InMemoryPayloadRepository(
        payloads={
            "event_7": {
                "world_time": 207,
                "verb": "LIKED",
                "subject_uuid": "agent_x",
                "target_ref": "event_6",
                "details": {},
                "schema_version": 1,
                "is_social": True,
            },
            "event_6": {
                "world_time": 206,
                "verb": "POSTED",
                "subject_uuid": "agent_me",
                "target_ref": "board:session_demo",
                "details": {"content": "hello"},
                "schema_version": 1,
                "is_social": True,
            },
            "event_5": {
                "world_time": 205,
                "verb": "POSTED",
                "subject_uuid": "agent_followed",
                "target_ref": "board:session_demo",
                "details": {"content": "followed"},
                "schema_version": 1,
                "is_social": True,
            },
            "event_4": {
                "world_time": 204,
                "verb": "POSTED",
                "subject_uuid": "agent_other",
                "target_ref": "board:session_demo",
                "details": {"content": "public"},
                "schema_version": 1,
                "is_social": True,
            },
            "event_3": {
                "world_time": 203,
                "verb": "FOLLOWED",
                "subject_uuid": "agent_me",
                "target_ref": "agent_followed",
                "details": {},
                "schema_version": 1,
                "is_social": True,
            },
            "event_2": {
                "world_time": 202,
                "verb": "REPLIED",
                "subject_uuid": "agent_x",
                "target_ref": "event_6",
                "details": {"content": "to me"},
                "schema_version": 1,
                "is_social": True,
            },
            "event_1": {
                "world_time": 201,
                "verb": "FOLLOWED",
                "subject_uuid": "agent_x",
                "target_ref": "agent:agent_me",
                "details": {},
                "schema_version": 1,
                "is_social": True,
            },
        }
    )
    graph_repo = InMemoryGraphRepository(
        event_ids=[
            "event_7",
            "event_6",
            "event_5",
            "event_4",
            "event_3",
            "event_2",
            "event_1",
        ]
    )
    usecase = GetAgentContextUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        payload_repo,
        graph_repo,
    )

    result = await usecase.execute(
        session_id="session_demo",
        agent_id="agent_me",
        limit=50,
    )

    assert result.session_id == "session_demo"
    assert result.agent_id == "agent_me"
    assert result.current_world_time == 207
    assert [item.event_id for item in result.views.self_recent.items] == ["event_6", "event_3"]
    assert [item.event_id for item in result.views.attention.items] == ["event_7", "event_2", "event_1"]
    assert [item.event_id for item in result.views.following_feed.items] == ["event_5"]
    assert [item.event_id for item in result.views.public_feed.items] == ["event_4"]
    assert result.views.self_recent.next_cursor is None
    assert result.views.self_recent.has_more is False
    assert result.views.following_feed.next_cursor is None
    assert result.views.following_feed.has_more is False
    assert result.views.hot.next_cursor is None
    assert result.views.hot.has_more is False
    assert result.views.hot.items[0].topic_ref == "board:session_demo"
    assert result.views.hot.items[0].score == 3.0
    assert result.views.hot.items[0].sample_event_ids == ["event_6", "event_5", "event_4"]
    assert result.views.world_snapshot.online_agents == 1
    assert result.views.world_snapshot.active_agents == 1
    assert result.views.world_snapshot.recent_event_count == 7
    assert result.views.world_snapshot.my_following_count == 1


@pytest.mark.asyncio
async def test_get_agent_context_usecase_sets_has_more_and_next_cursor() -> None:
    """验证事件类视图在超限时会返回分页标记。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    presence_repo = InMemoryPresenceRepository(active_ids={"agent_me"})
    profile_repo = InMemoryProfileRepository(existing_ids={"agent_me"})
    payload_repo = InMemoryPayloadRepository(
        payloads={
            "event_3": {
                "world_time": 203,
                "verb": "POSTED",
                "subject_uuid": "agent_me",
                "target_ref": "board:session_demo",
                "details": {"content": "3"},
                "schema_version": 1,
                "is_social": True,
            },
            "event_2": {
                "world_time": 202,
                "verb": "POSTED",
                "subject_uuid": "agent_me",
                "target_ref": "board:session_demo",
                "details": {"content": "2"},
                "schema_version": 1,
                "is_social": True,
            },
            "event_1": {
                "world_time": 201,
                "verb": "POSTED",
                "subject_uuid": "agent_me",
                "target_ref": "board:session_demo",
                "details": {"content": "1"},
                "schema_version": 1,
                "is_social": True,
            },
        }
    )
    graph_repo = InMemoryGraphRepository(event_ids=["event_3", "event_2", "event_1"])
    usecase = GetAgentContextUseCase(
        session_repo,
        presence_repo,
        profile_repo,
        payload_repo,
        graph_repo,
    )

    result = await usecase.execute(
        session_id="session_demo",
        agent_id="agent_me",
        limit=1,
    )

    assert [item.event_id for item in result.views.self_recent.items] == ["event_3"]
    assert result.views.self_recent.has_more is True
    assert result.views.self_recent.next_cursor == "203:event_3"


@pytest.mark.asyncio
async def test_get_agent_context_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    usecase = GetAgentContextUseCase(
        InMemorySessionRepository(),
        InMemoryPresenceRepository(active_ids={"agent_me"}),
        InMemoryProfileRepository(existing_ids={"agent_me"}),
        InMemoryPayloadRepository(payloads={}),
        InMemoryGraphRepository(event_ids=[]),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(session_id="session_missing", agent_id="agent_me")


@pytest.mark.asyncio
async def test_get_agent_context_usecase_raises_when_agent_missing() -> None:
    """验证 Agent 不存在时会抛出异常。"""
    session_repo = InMemorySessionRepository()
    await session_repo.create(
        session_id="session_demo",
        description=None,
        max_agents_limit=100,
    )
    usecase = GetAgentContextUseCase(
        session_repo,
        InMemoryPresenceRepository(active_ids=set()),
        InMemoryProfileRepository(existing_ids=set()),
        InMemoryPayloadRepository(payloads={}),
        InMemoryGraphRepository(event_ids=[]),
    )

    with pytest.raises(AgentNotFoundException):
        await usecase.execute(session_id="session_demo", agent_id="agent_missing")
