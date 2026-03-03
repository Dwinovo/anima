from __future__ import annotations

SESSION_KEY_PREFIX = "anima:session:"
ACTIVE_AGENTS_KEY_PREFIX = SESSION_KEY_PREFIX
ACTIVE_AGENTS_KEY_SUFFIX = ":active_agents"
DISPLAY_NAME_KEY_SUFFIX = ":display_name:"


def active_agents_key(session_id: str) -> str:
    # 在线 Agent 集合（Set）
    """执行 `active_agents_key` 相关逻辑。"""
    return f"{ACTIVE_AGENTS_KEY_PREFIX}{session_id}{ACTIVE_AGENTS_KEY_SUFFIX}"


def agent_profile_key(session_id: str, agent_id: str) -> str:
    # 单个 Agent 运行态（String JSON）
    """执行 `agent_profile_key` 相关逻辑。"""
    return f"anima:agent:{session_id}:{agent_id}"


def display_name_key(session_id: str, display_name: str) -> str:
    # 展示名唯一索引（String -> agent_id）
    """执行 `display_name_key` 相关逻辑。"""
    return f"{SESSION_KEY_PREFIX}{session_id}{DISPLAY_NAME_KEY_SUFFIX}{display_name}"
