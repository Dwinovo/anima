from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final


class SocialActionVerb(StrEnum):
    """社交动作枚举。"""

    POSTED = "POSTED"
    REPLIED = "REPLIED"
    QUOTED = "QUOTED"
    LIKED = "LIKED"
    DISLIKED = "DISLIKED"
    OBSERVED = "OBSERVED"
    FOLLOWED = "FOLLOWED"
    BLOCKED = "BLOCKED"


class TargetTopology(StrEnum):
    """Target 拓扑类型。"""

    BOARD = "board"
    AGENT = "agent"
    EVENT = "event"


@dataclass(slots=True, frozen=True)
class SocialActionCommand:
    """模型决策后统一的社交动作命令。"""

    verb: SocialActionVerb
    target_ref: str
    details: dict[str, Any]
    inner_thought_brief: str
    is_social: bool = True


SOCIAL_ACTION_TARGET_RULES: Final[dict[SocialActionVerb, frozenset[TargetTopology]]] = {
    SocialActionVerb.POSTED: frozenset({TargetTopology.BOARD}),
    SocialActionVerb.REPLIED: frozenset({TargetTopology.EVENT}),
    SocialActionVerb.QUOTED: frozenset({TargetTopology.EVENT}),
    SocialActionVerb.LIKED: frozenset({TargetTopology.EVENT}),
    SocialActionVerb.DISLIKED: frozenset({TargetTopology.EVENT}),
    SocialActionVerb.OBSERVED: frozenset(
        {
            TargetTopology.BOARD,
            TargetTopology.AGENT,
            TargetTopology.EVENT,
        }
    ),
    SocialActionVerb.FOLLOWED: frozenset({TargetTopology.AGENT}),
    SocialActionVerb.BLOCKED: frozenset({TargetTopology.AGENT}),
}


def build_board_ref(*, session_id: str) -> str:
    """构造当前 Session 公共广场引用。"""
    return f"board:{session_id}"


def resolve_target_topology(*, session_id: str, target_ref: str) -> TargetTopology:
    """根据目标引用解析拓扑类型。"""
    if target_ref == build_board_ref(session_id=session_id):
        return TargetTopology.BOARD
    if target_ref.startswith("event_"):
        return TargetTopology.EVENT
    return TargetTopology.AGENT


def is_target_allowed_for_verb(
    *,
    verb: SocialActionVerb,
    session_id: str,
    target_ref: str,
) -> bool:
    """判断目标引用是否符合动作拓扑约束。"""
    target_topology = resolve_target_topology(session_id=session_id, target_ref=target_ref)
    allowed_topologies = SOCIAL_ACTION_TARGET_RULES[verb]
    return target_topology in allowed_topologies


__all__ = [
    "SocialActionVerb",
    "TargetTopology",
    "SocialActionCommand",
    "SOCIAL_ACTION_TARGET_RULES",
    "build_board_ref",
    "resolve_target_topology",
    "is_target_allowed_for_verb",
]
