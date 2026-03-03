from __future__ import annotations

import json
from hashlib import sha1

from src.application.dto.agent import AgentLifecycleResult
from src.core.exceptions import (
    AgentNotFoundException,
    DisplayNameAllocationException,
    SessionNotFoundException,
)
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.session.repository import SessionRepository

DISPLAY_NAME_SPACE_SIZE = 100000


class PatchAgentUseCase:
    """更新 Agent 昵称并重算唯一展示名。"""

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

    async def execute(self, *, session_id: str, agent_id: str, name: str) -> AgentLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        profile_json = await self._profile_repo.get(session_id=session_id, agent_id=agent_id)
        is_active = await self._presence_repo.is_active(session_id=session_id, agent_id=agent_id)
        if profile_json is None and not is_active:
            raise AgentNotFoundException(session_id=session_id, uuid=agent_id)

        current = self._parse_profile_payload(profile_json)
        base_suffix = self._suffix_seed(session_id=session_id, agent_id=agent_id)
        display_name = await self._allocate_unique_display_name(
            session_id=session_id,
            agent_id=agent_id,
            name=name,
            base_suffix=base_suffix,
        )

        previous_display_name = current.get("display_name")
        if previous_display_name and previous_display_name != display_name:
            await self._profile_repo.release_display_name(
                session_id=session_id,
                agent_id=agent_id,
                display_name=previous_display_name,
            )

        updated_profile_payload = {
            "name": name,
            "display_name": display_name,
            "active": is_active,
            "profile": current.get("profile"),
        }
        updated_profile_json = json.dumps(updated_profile_payload, ensure_ascii=False, separators=(",", ":"))
        await self._profile_repo.save(
            session_id=session_id,
            agent_id=agent_id,
            profile_json=updated_profile_json,
        )

        return AgentLifecycleResult(
            session_id=session_id,
            agent_id=agent_id,
            active=is_active,
            name=name,
            display_name=display_name,
            profile=current.get("profile"),
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

        display_name = payload.get("display_name")
        profile = payload.get("profile")
        return {
            "name": payload.get("name") if isinstance(payload.get("name"), str) else None,
            "display_name": display_name if isinstance(display_name, str) else None,
            "profile": profile if isinstance(profile, str) else None,
        }
