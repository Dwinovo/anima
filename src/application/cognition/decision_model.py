from __future__ import annotations

from typing import Any, Protocol

from src.application.dto.event import EventSearchItem
from src.domain.agent.social_actions import SocialActionCommand


class SocialDecisionModel(Protocol):
    """社交动作决策模型接口。"""

    async def decide(
        self,
        *,
        session_id: str,
        uuid: str,
        prompt: str,
        profile_payload: dict[str, Any],
        working_memory: list[str],
        observation_items: list[EventSearchItem],
    ) -> SocialActionCommand:
        """基于上下文做出动作决策并返回统一命令。"""
        ...
