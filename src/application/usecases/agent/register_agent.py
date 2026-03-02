from __future__ import annotations

import json
from hashlib import sha1
from typing import Any

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
    def _suffix_seed(*, session_id: str, uuid: str) -> int:
        """基于 session_id+uuid 生成稳定的数字后缀起点。"""
        digest = sha1(f"{session_id}:{uuid}".encode("utf-8"), usedforsecurity=False).hexdigest()
        return int(digest[:8], 16) % DISPLAY_NAME_SPACE_SIZE

    @staticmethod
    def _build_display_name(*, name: str, suffix_number: int) -> str:
        """根据昵称与后缀拼接展示名。"""
        return f"{name}#{suffix_number:05d}"

    async def execute(
        self,
        *,
        session_id: str,
        uuid: str,
        name: str,
        profile: dict[str, Any],
    ) -> AgentLifecycleResult:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        already_active = await self._presence_repo.is_active(session_id=session_id, uuid=uuid)
        if not already_active:
            active_count = await self._presence_repo.count_active(session_id=session_id)
            if active_count >= session.max_agents_limit:
                raise QuotaExceededException(session_id=session_id, limit=session.max_agents_limit)
            await self._presence_repo.activate(session_id=session_id, uuid=uuid)

        existing_profile_json = await self._profile_repo.get(session_id=session_id, uuid=uuid)
        previous_display_name = self._extract_display_name(existing_profile_json)

        base_suffix = self._suffix_seed(session_id=session_id, uuid=uuid)
        display_name = await self._allocate_unique_display_name(
            session_id=session_id,
            uuid=uuid,
            name=name,
            base_suffix=base_suffix,
        )

        if previous_display_name is not None and previous_display_name != display_name:
            await self._profile_repo.release_display_name(
                session_id=session_id,
                uuid=uuid,
                display_name=previous_display_name,
            )

        profile_payload = {
            "name": name,
            "display_name": display_name,
            "profile": profile,
        }
        profile_json = json.dumps(profile_payload, ensure_ascii=False, separators=(",", ":"))
        await self._profile_repo.save(
            session_id=session_id,
            uuid=uuid,
            profile_json=profile_json,
        )
        return AgentLifecycleResult(
            session_id=session_id,
            uuid=uuid,
            active=True,
            name=name,
            display_name=display_name,
        )

    async def _allocate_unique_display_name(
        self,
        *,
        session_id: str,
        uuid: str,
        name: str,
        base_suffix: int,
    ) -> str:
        """分配同 Session 内唯一展示名，不可用时线性探测后缀空间。"""
        for offset in range(DISPLAY_NAME_SPACE_SIZE):
            suffix = (base_suffix + offset) % DISPLAY_NAME_SPACE_SIZE
            candidate = self._build_display_name(name=name, suffix_number=suffix)
            claimed = await self._profile_repo.claim_display_name(
                session_id=session_id,
                uuid=uuid,
                display_name=candidate,
            )
            if claimed:
                return candidate
        raise DisplayNameAllocationException(session_id=session_id, name=name)

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
