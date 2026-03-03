from __future__ import annotations

from src.main import app


def test_session_events_get_api_is_exposed() -> None:
    """验证会话事件列表 GET 接口已对外暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}/events" and "GET" in methods:
            route_found = True
            break
    assert route_found is True
