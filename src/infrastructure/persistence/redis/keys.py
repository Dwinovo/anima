from __future__ import annotations

SESSION_KEY_PREFIX = "anima:session:"
ACTIVE_AGENTS_KEY_PREFIX = SESSION_KEY_PREFIX
ACTIVE_AGENTS_KEY_SUFFIX = ":active_agents"
DISPLAY_NAME_KEY_SUFFIX = ":display_name:"


def active_agents_key(session_id: str) -> str:
    # 在线 Agent 集合（Set）
    """执行 `active_agents_key` 相关逻辑。"""
    return f"{ACTIVE_AGENTS_KEY_PREFIX}{session_id}{ACTIVE_AGENTS_KEY_SUFFIX}"


def agent_profile_key(session_id: str, uuid: str) -> str:
    # 单个 Agent 的 Profile（String JSON）
    """执行 `agent_profile_key` 相关逻辑。"""
    return f"anima:agent:{session_id}:{uuid}:profile"


def display_name_key(session_id: str, display_name: str) -> str:
    # 展示名唯一索引（String -> uuid）
    """执行 `display_name_key` 相关逻辑。"""
    return f"{SESSION_KEY_PREFIX}{session_id}{DISPLAY_NAME_KEY_SUFFIX}{display_name}"


def checkpoint_key(session_id: str, uuid: str) -> str:
    # LangGraph checkpoint（String JSON + TTL）
    """执行 `checkpoint_key` 相关逻辑。"""
    return f"anima:checkpoint:{session_id}:{uuid}"
