from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.requests.agent import AgentPatchRequest, AgentRegisterRequest


def test_agent_register_request_accepts_name_and_profile() -> None:
    """验证注册请求接受 name+profile。"""
    payload = {
        "name": "Alice",
        "profile": "我是一个理性且克制的观察者。",
    }

    request = AgentRegisterRequest.model_validate(payload)

    assert request.name == "Alice"
    assert request.profile == "我是一个理性且克制的观察者。"


def test_agent_register_request_rejects_blank_profile() -> None:
    """验证 profile 为空会返回明确错误。"""
    with pytest.raises(ValidationError):
        AgentRegisterRequest.model_validate(
            {
                "name": "Alice",
                "profile": "   ",
            }
        )


def test_agent_patch_request_accepts_name() -> None:
    """验证 Agent PATCH 仅修改 name。"""
    request = AgentPatchRequest.model_validate({"name": "AliceNew"})
    assert request.name == "AliceNew"
    assert request.profile is None


def test_agent_patch_request_accepts_profile_only() -> None:
    """验证 Agent PATCH 支持仅修改 profile。"""
    request = AgentPatchRequest.model_validate({"profile": "新的名片"})
    assert request.name is None
    assert request.profile == "新的名片"


def test_agent_patch_request_rejects_empty_payload() -> None:
    """验证 Agent PATCH 空请求会被拒绝。"""
    with pytest.raises(ValidationError):
        AgentPatchRequest.model_validate({})
