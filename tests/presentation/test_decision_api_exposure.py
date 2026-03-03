from __future__ import annotations

from src.main import app


def test_decision_api_is_not_exposed() -> None:
    """验证外部路由中不暴露 Agent 决策触发接口。"""
    hidden_path = "/api/v1/sessions/{session_id}/agents/{agent_id}/decisions"
    route_paths = {route.path for route in app.routes}
    assert hidden_path not in route_paths
