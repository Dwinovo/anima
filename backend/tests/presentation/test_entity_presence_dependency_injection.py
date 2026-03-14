from __future__ import annotations

from fastapi.routing import APIWebSocketRoute

from src.main import app


def test_entity_presence_websocket_uses_compound_auth_dependency() -> None:
    """WebSocket presence 路由应使用统一鉴权依赖，而非直接注入底层依赖。"""
    route = next(
        candidate
        for candidate in app.routes
        if isinstance(candidate, APIWebSocketRoute)
        and candidate.path == "/api/v1/sessions/{session_id}/entities/{entity_id}/presence"
    )

    dependency_names = [dependency.call.__name__ for dependency in route.dependant.dependencies]

    assert "require_entity_ws_access_claims" in dependency_names
    assert "get_token_service" not in dependency_names
    assert "get_auth_state_repo" not in dependency_names
