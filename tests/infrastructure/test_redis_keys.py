from __future__ import annotations

from src.infrastructure.persistence.redis.keys import (
    active_agents_key,
    agent_profile_key,
    checkpoint_key,
    display_name_key,
)


def test_active_agents_key_uses_session_namespace() -> None:
    """验证在线集合 key 的命名规范。"""
    assert active_agents_key("session_demo") == "anima:session:session_demo:active_agents"


def test_agent_profile_key_uses_agent_namespace() -> None:
    """验证画像 key 的命名规范。"""
    assert agent_profile_key("session_demo", "agent_001") == "anima:agent:session_demo:agent_001:profile"


def test_display_name_key_uses_session_namespace() -> None:
    """验证展示名索引 key 的命名规范。"""
    assert (
        display_name_key("session_demo", "Alice#48291")
        == "anima:session:session_demo:display_name:Alice#48291"
    )


def test_checkpoint_key_uses_namespace() -> None:
    """验证 LangGraph checkpoint key 的命名规范。"""
    assert checkpoint_key("session_demo", "agent_001") == "anima:checkpoint:session_demo:agent_001"
