from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.requests.session import SessionCreateRequest, SessionPatchRequest


def test_session_create_request_accepts_core_fields() -> None:
    """验证创建 Session 仅需核心字段。"""
    payload = {
        "name": "Alpha Session",
        "description": "demo",
        "max_agents_limit": 100,
    }

    request = SessionCreateRequest.model_validate(payload)

    assert request.name == "Alpha Session"
    assert request.max_agents_limit == 100


def test_session_create_request_rejects_client_session_id() -> None:
    """验证创建请求不允许客户端自带 session_id。"""
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "session_id": "session_alpha",
                "max_agents_limit": 100,
            }
        )


def test_session_patch_request_accepts_core_patch_fields() -> None:
    """验证 PATCH 仅支持核心字段增量更新。"""
    request = SessionPatchRequest.model_validate(
        {
            "name": "Alpha2",
            "description": "Alpha2",
            "max_agents_limit": 120,
        }
    )
    assert request.name == "Alpha2"
    assert request.description == "Alpha2"
    assert request.max_agents_limit == 120
