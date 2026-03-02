from __future__ import annotations

from typing import Any

from src.application.cognition.decision_model import SocialDecisionModel
from src.application.dto.event import EventSearchItem
from src.domain.agent.social_actions import SocialActionCommand, build_board_ref
from src.infrastructure.llm.tool_calling.social_actions import parse_social_action_tool_call


class RuleBasedSocialDecisionModel(SocialDecisionModel):
    """规则版决策模型（LangGraph 第一版占位实现）。"""

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
        """输出一个保守的 OBSERVED 动作，后续可替换为真实 LLM Tool Calling。"""
        _ = (uuid, prompt, profile_payload, working_memory)
        latest_verb = observation_items[0].verb if observation_items else None
        if isinstance(latest_verb, str) and latest_verb:
            inner_thought_brief = f"先观察{latest_verb}后的局势"
        else:
            inner_thought_brief = "先观察局势"
        inner_thought_brief = inner_thought_brief[:48]

        return parse_social_action_tool_call(
            session_id=session_id,
            tool_name="social_observed",
            arguments={
                "target_ref": build_board_ref(session_id=session_id),
                "internal_thought": "先记录当前局势，再决定下一步社交动作。",
                "inner_thought_brief": inner_thought_brief,
            },
        )
