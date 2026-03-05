from __future__ import annotations

SESSION_KEY_PREFIX = "anima:session:"
ACTIVE_ENTITIES_KEY_PREFIX = SESSION_KEY_PREFIX
ACTIVE_ENTITIES_KEY_SUFFIX = ":active_entities"
DISPLAY_NAME_KEY_SUFFIX = ":display_name:"
HEARTBEAT_KEY_MIDDLE = ":entity:"
HEARTBEAT_KEY_SUFFIX = ":heartbeat"
AUTH_KEY_PREFIX = "anima:auth:"
AUTH_TOKEN_VERSION_KEY_PREFIX = f"{AUTH_KEY_PREFIX}token_version:"
AUTH_REFRESH_KEY_PREFIX = f"{AUTH_KEY_PREFIX}refresh:"
AUTH_REFRESH_INDEX_KEY_PREFIX = f"{AUTH_KEY_PREFIX}refresh_index:"


def active_entities_key(session_id: str) -> str:
    # 在线 Entity 集合（Set）
    """执行 `active_entities_key` 相关逻辑。"""
    return f"{ACTIVE_ENTITIES_KEY_PREFIX}{session_id}{ACTIVE_ENTITIES_KEY_SUFFIX}"


def entity_profile_key(session_id: str, entity_id: str) -> str:
    # 单个 Entity 运行态（String JSON）
    """执行 `entity_profile_key` 相关逻辑。"""
    return f"anima:entity:{session_id}:{entity_id}"


def display_name_key(session_id: str, display_name: str) -> str:
    # 展示名唯一索引（String -> entity_id）
    """执行 `display_name_key` 相关逻辑。"""
    return f"{SESSION_KEY_PREFIX}{session_id}{DISPLAY_NAME_KEY_SUFFIX}{display_name}"


def heartbeat_key(session_id: str, entity_id: str) -> str:
    # Entity 在线心跳键（String + TTL）
    """执行 `heartbeat_key` 相关逻辑。"""
    return f"{SESSION_KEY_PREFIX}{session_id}{HEARTBEAT_KEY_MIDDLE}{entity_id}{HEARTBEAT_KEY_SUFFIX}"


def auth_token_version_key(session_id: str, entity_id: str) -> str:
    # Entity token_version（String）
    """执行 `auth_token_version_key` 相关逻辑。"""
    return f"{AUTH_TOKEN_VERSION_KEY_PREFIX}{session_id}:{entity_id}"


def auth_refresh_token_key(session_id: str, entity_id: str, refresh_jti: str) -> str:
    # Entity refresh token jti（String + TTL）
    """执行 `auth_refresh_token_key` 相关逻辑。"""
    return f"{AUTH_REFRESH_KEY_PREFIX}{session_id}:{entity_id}:{refresh_jti}"


def auth_refresh_index_key(session_id: str, entity_id: str) -> str:
    # Entity refresh_jti 索引（Set）
    """执行 `auth_refresh_index_key` 相关逻辑。"""
    return f"{AUTH_REFRESH_INDEX_KEY_PREFIX}{session_id}:{entity_id}"
