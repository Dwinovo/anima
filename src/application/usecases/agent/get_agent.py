from __future__ import annotations

import json

from src.application.dto.agent import AgentLifecycleResult
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.session.repository import SessionRepository


class GetAgentUseCase:
    """查询指定 Agent 当前信息。"""

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

        profile_json = await self._profile_repo.get(session_id=session_id, agent_id=agent_id)
        is_active = await self._presence_repo.is_active(session_id=session_id, agent_id=agent_id)
        if profile_json is None and not is_active:
            raise AgentNotFoundException(session_id=session_id, uuid=agent_id)

        parsed = self._parse_profile_payload(profile_json)
        return AgentLifecycleResult(
            session_id=session_id,
            agent_id=agent_id,
            active=is_active,
            name=parsed.get("name"),
            display_name=parsed.get("display_name"),
            profile=parsed.get("profile"),
        )

    @staticmethod
    def _parse_profile_payload(profile_json: str | None) -> dict[str, str | None]:
        """解析 Redis 画像缓存为结构化字段。"""
        if profile_json is None:
            return {"name": None, "display_name": None, "profile": None}

        try:
            payload = json.loads(profile_json)
        except json.JSONDecodeError:
            return {"name": None, "display_name": None, "profile": None}

        if not isinstance(payload, dict):
            return {"name": None, "display_name": None, "profile": None}

        name = payload.get("name")
        display_name = payload.get("display_name")
        profile = payload.get("profile")
        return {
            "name": name if isinstance(name, str) else None,
            "display_name": display_name if isinstance(display_name, str) else None,
            "profile": profile if isinstance(profile, str) else None,
        }
