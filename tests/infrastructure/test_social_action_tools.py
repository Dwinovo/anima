from __future__ import annotations

import pytest

from src.domain.agent.social_actions import SocialActionVerb
from src.infrastructure.llm.tool_calling.social_actions import (
    InvalidSocialActionToolCallError,
    build_social_action_tools,
    parse_social_action_tool_call,
)


def test_build_social_action_tools_contains_all_eight_actions() -> None:
    """验证 Tool Calling 定义覆盖 8 大社交动作。"""
    tools = build_social_action_tools()
    tool_names = {tool["function"]["name"] for tool in tools}
    assert tool_names == {
        "social_posted",
        "social_replied",
        "social_quoted",
        "social_liked",
        "social_disliked",
        "social_observed",
        "social_followed",
        "social_blocked",
    }


def test_parse_social_action_tool_call_maps_to_event_command() -> None:
    """验证工具调用可被解析成统一社交动作命令。"""
    command = parse_social_action_tool_call(
        session_id="session_demo",
        tool_name="social_posted",
        arguments={
            "content": "hello anima",
            "inner_thought_brief": "先发到广场试探反应",
        },
    )
    assert command.verb is SocialActionVerb.POSTED
    assert command.target_ref == "board:session_demo"
    assert command.details["content"] == "hello anima"
    assert command.inner_thought_brief == "先发到广场试探反应"


def test_parse_social_action_tool_call_rejects_invalid_topology() -> None:
    """验证不符合拓扑约束的工具参数会被拒绝。"""
    with pytest.raises(InvalidSocialActionToolCallError):
        parse_social_action_tool_call(
            session_id="session_demo",
            tool_name="social_followed",
            arguments={
                "target_ref": "event_x",
                "inner_thought_brief": "这个对象像是值得关注",
            },
        )


def test_parse_social_action_tool_call_requires_inner_thought_brief() -> None:
    """验证内心摘要字段缺失时会被拒绝。"""
    with pytest.raises(InvalidSocialActionToolCallError):
        parse_social_action_tool_call(
            session_id="session_demo",
            tool_name="social_liked",
            arguments={
                "target_ref": "event_x",
            },
        )
