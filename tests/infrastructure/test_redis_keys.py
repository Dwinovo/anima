from __future__ import annotations

from src.infrastructure.persistence.redis.keys import (
    active_entities_key,
    auth_refresh_index_key,
    auth_refresh_token_key,
    auth_token_version_key,
    display_name_key,
    entity_profile_key,
    heartbeat_key,
)


def test_active_entities_key_uses_session_namespace() -> None:
    """验证在线集合 key 的命名规范。"""
    assert active_entities_key("session_demo") == "anima:session:session_demo:active_entities"


def test_entity_profile_key_uses_entity_namespace() -> None:
    """验证画像 key 的命名规范。"""
    assert entity_profile_key("session_demo", "entity_001") == "anima:entity:session_demo:entity_001"


def test_display_name_key_uses_session_namespace() -> None:
    """验证展示名索引 key 的命名规范。"""
    assert (
        display_name_key("session_demo", "Alice#48291")
        == "anima:session:session_demo:display_name:Alice#48291"
    )


def test_heartbeat_key_uses_session_and_entity_namespace() -> None:
    """验证心跳 key 的命名规范。"""
    assert (
        heartbeat_key("session_demo", "entity_001")
        == "anima:session:session_demo:entity:entity_001:heartbeat"
    )


def test_auth_token_version_key_uses_session_and_entity_namespace() -> None:
    """验证 token_version key 的命名规范。"""
    assert (
        auth_token_version_key("session_demo", "entity_001")
        == "anima:auth:token_version:session_demo:entity_001"
    )


def test_auth_refresh_token_key_uses_refresh_jti_namespace() -> None:
    """验证 refresh token key 的命名规范。"""
    assert (
        auth_refresh_token_key("session_demo", "entity_001", "jti_123")
        == "anima:auth:refresh:session_demo:entity_001:jti_123"
    )


def test_auth_refresh_index_key_uses_session_and_entity_namespace() -> None:
    """验证 refresh 索引 key 的命名规范。"""
    assert (
        auth_refresh_index_key("session_demo", "entity_001")
        == "anima:auth:refresh_index:session_demo:entity_001"
    )
