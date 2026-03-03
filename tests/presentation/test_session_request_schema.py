from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.requests.session import SessionCreateRequest, SessionPatchRequest


def test_session_create_request_accepts_core_fields() -> None:
    """验证创建 Session 仅需核心字段。"""
    payload = {
        "session_id": "session_alpha",
        "description": "demo",
        "max_agents_limit": 100,
    }

    request = SessionCreateRequest.model_validate(payload)

    assert request.session_id == "session_alpha"
    assert request.max_agents_limit == 100


def test_session_create_request_rejects_scheduler_fields() -> None:
    """验证调度字段已从创建请求模型移除。"""
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                "session_id": "session_alpha",
                "max_agents_limit": 100,
                "scheduler_enabled": True,
            }
        )


def test_session_patch_request_accepts_core_patch_fields() -> None:
    """验证 PATCH 仅支持核心字段增量更新。"""
    request = SessionPatchRequest.model_validate(
        {
            "description": "Alpha2",
            "max_agents_limit": 120,
        }
    )
    assert request.description == "Alpha2"
    assert request.max_agents_limit == 120
