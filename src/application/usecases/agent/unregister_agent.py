from __future__ import annotations

import json

from src.application.dto.agent import AgentLifecycleResult
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.session.repository import SessionRepository


class UnregisterAgentUseCase:
    """从指定 Session 卸载 Agent。"""

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

    async def execute(self, *, session_id: str, agent_id: str) -> AgentLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        is_active = await self._presence_repo.is_active(session_id=session_id, agent_id=agent_id)
        profile = await self._profile_repo.get(session_id=session_id, agent_id=agent_id)
        if not is_active and profile is None:
            raise AgentNotFoundException(session_id=session_id, uuid=agent_id)

        display_name = self._extract_display_name(profile)
        if display_name is not None:
            await self._profile_repo.release_display_name(
                session_id=session_id,
                agent_id=agent_id,
                display_name=display_name,
            )
        await self._presence_repo.deactivate(session_id=session_id, agent_id=agent_id)
        await self._profile_repo.delete(session_id=session_id, agent_id=agent_id)
        return AgentLifecycleResult(
            session_id=session_id,
            agent_id=agent_id,
            active=False,
        )

    @staticmethod
    def _extract_display_name(profile_json: str | None) -> str | None:
        """从既有 profile 缓存中提取 display_name。"""
        if profile_json is None:
            return None
        try:
            payload = json.loads(profile_json)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        display_name = payload.get("display_name")
        if isinstance(display_name, str) and display_name:
            return display_name
        return None
