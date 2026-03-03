from __future__ import annotations

from src.main import app


def test_social_actions_get_api_is_exposed() -> None:
    """验证社交动作元信息 GET 接口已暴露。"""
    route_found = False
    for route in app.routes:
        methods = getattr(route, "methods", set())
        if route.path == "/api/v1/social-actions" and "GET" in methods:
            route_found = True
            break
    assert route_found is True
