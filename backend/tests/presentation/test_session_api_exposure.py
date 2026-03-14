from __future__ import annotations

from src.main import app


def test_session_get_api_is_exposed() -> None:
    """验证 Session 详情 GET 接口已暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}" and "GET" in methods:
            route_found = True
            break
    assert route_found is True


def test_session_patch_api_is_exposed() -> None:
    """验证 Session PATCH 接口已暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}" and "PATCH" in methods:
            route_found = True
            break
    assert route_found is True


def test_session_scheduler_subresource_api_is_not_exposed() -> None:
    """验证 scheduler-config 子资源路由已移除。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/sessions/{session_id}/scheduler-config" and (
            "GET" in methods or "PATCH" in methods
        ):
            route_found = True
            break
    assert route_found is False
