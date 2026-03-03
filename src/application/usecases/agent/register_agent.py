from __future__ import annotations

import json
from hashlib import sha1
from uuid import uuid4

from src.application.dto.agent import AgentLifecycleResult
from src.core.exceptions import (
    DisplayNameAllocationException,
    QuotaExceededException,
    SessionNotFoundException,
)
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.session.repository import SessionRepository

DISPLAY_NAME_SPACE_SIZE = 100000


class RegisterAgentUseCase:
    """注册 Agent 到指定 Session。"""

    def __init__(
        self,
        session_repo: SessionRepository,
        presence_repo: AgentPresenceRepository,
        profile_repo: AgentProfileRepository,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._presence_repo = presence_repo
        self._profile_repo = profile_repo

    @staticmethod
    def _suffix_seed(*, session_id: str, agent_id: str) -> int:
        """基于 session_id+agent_id 生成稳定的数字后缀起点。"""
        digest = sha1(f"{session_id}:{agent_id}".encode("utf-8"), usedforsecurity=False).hexdigest()
        return int(digest[:8], 16) % DISPLAY_NAME_SPACE_SIZE

    @staticmethod
    def _build_display_name(*, name: str, suffix_number: int) -> str:
        """根据昵称与后缀拼接展示名。"""
        return f"{name}#{suffix_number:05d}"

    async def execute(
        self,
        *,
        session_id: str,
        name: str,
        profile: str,
    ) -> AgentLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        active_count = await self._presence_repo.count_active(session_id=session_id)
        if active_count >= session.max_agents_limit:
            raise QuotaExceededException(session_id=session_id, limit=session.max_agents_limit)

        agent_id = str(uuid4())
        base_suffix = self._suffix_seed(session_id=session_id, agent_id=agent_id)
        display_name = await self._allocate_unique_display_name(
            session_id=session_id,
            agent_id=agent_id,
            name=name,
            base_suffix=base_suffix,
        )

        profile_payload = {
            "name": name,
            "display_name": display_name,
            "active": True,
            "profile": profile,
        }
        profile_json = json.dumps(profile_payload, ensure_ascii=False, separators=(",", ":"))
        await self._profile_repo.save(
            session_id=session_id,
            agent_id=agent_id,
            profile_json=profile_json,
        )
        await self._presence_repo.activate(session_id=session_id, agent_id=agent_id)
        return AgentLifecycleResult(
            session_id=session_id,
            agent_id=agent_id,
            active=True,
            name=name,
            display_name=display_name,
            profile=profile,
        )

    async def _allocate_unique_display_name(
        self,
        *,
        session_id: str,
        agent_id: str,
        name: str,
        base_suffix: int,
    ) -> str:
        """分配同 Session 内唯一展示名，不可用时线性探测后缀空间。"""
        for offset in range(DISPLAY_NAME_SPACE_SIZE):
            suffix = (base_suffix + offset) % DISPLAY_NAME_SPACE_SIZE
            candidate = self._build_display_name(name=name, suffix_number=suffix)
            claimed = await self._profile_repo.claim_display_name(
                session_id=session_id,
                agent_id=agent_id,
                display_name=candidate,
            )
            if claimed:
                return candidate
        raise DisplayNameAllocationException(session_id=session_id, name=name)
