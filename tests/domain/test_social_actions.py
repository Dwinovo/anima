from __future__ import annotations

from src.domain.agent.social_actions import (
    SOCIAL_ACTION_TARGET_RULES,
    SocialActionVerb,
    TargetTopology,
    build_board_ref,
    is_target_allowed_for_verb,
    resolve_target_topology,
)


def test_build_board_ref_returns_expected_pattern() -> None:
    """验证公共广场引用格式符合规范。"""
    assert build_board_ref(session_id="session_demo") == "board:session_demo"


def test_resolve_target_topology_prefers_board_and_event_patterns() -> None:
    """验证目标拓扑解析优先识别 board 和 event。"""
    assert resolve_target_topology(session_id="session_demo", target_ref="board:session_demo") is TargetTopology.BOARD
    assert resolve_target_topology(session_id="session_demo", target_ref="event_abcd") is TargetTopology.EVENT
    assert resolve_target_topology(session_id="session_demo", target_ref="agent_x") is TargetTopology.AGENT


def test_social_action_target_rules_cover_all_verbs() -> None:
    """验证所有社交动作都定义了目标拓扑约束。"""
    assert set(SOCIAL_ACTION_TARGET_RULES.keys()) == set(SocialActionVerb)


def test_replied_and_liked_must_target_event() -> None:
    """验证 REPLIED/LIKED 只能指向 Event。"""
    assert is_target_allowed_for_verb(
        verb=SocialActionVerb.REPLIED,
        session_id="session_demo",
        target_ref="event_x",
    )
    assert not is_target_allowed_for_verb(
        verb=SocialActionVerb.REPLIED,
        session_id="session_demo",
        target_ref="agent_x",
    )
    assert is_target_allowed_for_verb(
        verb=SocialActionVerb.LIKED,
        session_id="session_demo",
        target_ref="event_x",
    )
    assert not is_target_allowed_for_verb(
        verb=SocialActionVerb.LIKED,
        session_id="session_demo",
        target_ref="board:session_demo",
    )


def test_posted_must_target_board() -> None:
    """验证 POSTED 只能指向 board:{session_id}。"""
    assert is_target_allowed_for_verb(
        verb=SocialActionVerb.POSTED,
        session_id="session_demo",
        target_ref="board:session_demo",
    )
    assert not is_target_allowed_for_verb(
        verb=SocialActionVerb.POSTED,
        session_id="session_demo",
        target_ref="event_x",
    )
