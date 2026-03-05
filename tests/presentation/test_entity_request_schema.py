from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.requests.entity import EntityPatchRequest, EntityRegisterRequest


def test_entity_register_request_accepts_name_and_source() -> None:
    """验证注册请求需要 name 与 source。"""
    payload = {"name": "Alice", "source": "minecraft"}

    request = EntityRegisterRequest.model_validate(payload)

    assert request.name == "Alice"
    assert request.source == "minecraft"


def test_entity_register_request_rejects_extra_fields() -> None:
    """验证注册请求包含未知字段会被拒绝。"""
    with pytest.raises(ValidationError):
        EntityRegisterRequest.model_validate(
            {
                "name": "Alice",
                "source": "minecraft",
                "unknown": "x",
            }
        )


def test_entity_register_request_rejects_missing_source() -> None:
    """验证注册请求缺失 source 会被拒绝。"""
    with pytest.raises(ValidationError):
        EntityRegisterRequest.model_validate({"name": "Alice"})


def test_entity_patch_request_accepts_name() -> None:
    """验证 Entity PATCH 仅修改 name。"""
    request = EntityPatchRequest.model_validate({"name": "AliceNew"})
    assert request.name == "AliceNew"


def test_entity_patch_request_rejects_profile_field() -> None:
    """验证 Entity PATCH 不允许 profile 字段。"""
    with pytest.raises(ValidationError):
        EntityPatchRequest.model_validate({"profile": "新的名片"})


def test_entity_patch_request_rejects_empty_payload() -> None:
    """验证 Entity PATCH 空请求会被拒绝。"""
    with pytest.raises(ValidationError):
        EntityPatchRequest.model_validate({})
