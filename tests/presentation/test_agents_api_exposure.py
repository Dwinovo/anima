from __future__ import annotations

from starlette.routing import WebSocketRoute

from src.main import app


def test_agent_register_api_is_exposed() -> None:
    """验证 Agent 注册接口已暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}/agents" and "POST" in methods:
            route_found = True
            break
    assert route_found is True


def test_agent_crud_api_is_exposed() -> None:
    """验证 Agent 详情/编辑/下线接口已暴露。"""
    found_get = False
    found_patch = False
    found_delete = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}/agents/{agent_id}":
            found_get = found_get or "GET" in methods
            found_patch = found_patch or "PATCH" in methods
            found_delete = found_delete or "DELETE" in methods
    assert found_get is True
    assert found_patch is True
    assert found_delete is True


def test_agent_context_api_is_exposed() -> None:
    """验证 Agent Context 接口已暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}/agents/{agent_id}/context" and "GET" in methods:
            route_found = True
            break
    assert route_found is True


def test_agent_presence_websocket_api_is_exposed() -> None:
    """验证 Agent Presence WebSocket 接口已暴露。"""
    route_found = False
    for route in app.routes:
        if isinstance(route, WebSocketRoute) and route.path == "/api/v1/sessions/{session_id}/agents/{agent_id}/presence":
            route_found = True
            break
    assert route_found is True


def test_agent_token_refresh_api_is_exposed() -> None:
    """验证 Agent 刷新令牌接口已暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}/agents/{agent_id}/tokens/refresh" and "POST" in methods:
            route_found = True
            break
    assert route_found is True
