from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.session.actions import SessionAction
from src.presentation.api.schemas.requests.session import SessionCreateRequest, SessionPatchRequest
from src.presentation.api.schemas.session_action import SessionActionSchema


def build_actions_payload() -> list[dict[str, object]]:
    """构造最小合法 actions 请求体。"""
    return [
        {
            "verb": "social.posted",
            "description": "post to session board",
            "details_schema": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {
                        "type": "string",
                        "minLength": 1,
                        "description": "post content",
                    }
                },
                "additionalProperties": False,
            },
        }
    ]


def test_session_create_request_accepts_core_fields() -> None:
    """验证创建 Session 仅需核心字段。"""
    payload = {
        "name": "Alpha Session",
        "description": "demo",
        "max_entities_limit": 100,
        "actions": build_actions_payload(),
    }

    request = SessionCreateRequest.model_validate(payload)

    assert request.name == "Alpha Session"
    assert request.max_entities_limit == 100
    assert request.actions[0].verb == "social.posted"


def test_session_create_request_requires_actions() -> None:
    """验证创建 Session 时必须显式提交动作注册表。"""
    with pytest.raises(ValidationError) as exc_info:
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "description": "demo",
                "max_entities_limit": 100,
            }
        )

    assert any(error["loc"] == ("actions",) for error in exc_info.value.errors())


def test_session_create_request_accepts_empty_actions() -> None:
    """验证创建 Session 时 actions 可为空数组。"""
    request = SessionCreateRequest.model_validate(
        {
            "name": "Alpha Session",
            "description": "demo",
            "max_entities_limit": 100,
            "actions": [],
        }
    )

    assert request.actions == []


def test_session_create_request_rejects_client_session_id() -> None:
    """验证创建请求不允许客户端自带 session_id。"""
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "session_id": "session_alpha",
                "max_entities_limit": 100,
                "actions": build_actions_payload(),
            }
        )


def test_session_patch_request_accepts_core_patch_fields() -> None:
    """验证 PATCH 仅支持核心字段增量更新。"""
    request = SessionPatchRequest.model_validate(
        {
            "name": "Alpha2",
            "description": "Alpha2",
            "max_entities_limit": 120,
            "actions": build_actions_payload(),
        }
    )
    assert request.name == "Alpha2"
    assert request.description == "Alpha2"
    assert request.max_entities_limit == 120
    assert request.actions is not None
    assert request.actions[0].verb == "social.posted"


def test_session_patch_request_accepts_empty_actions() -> None:
    """验证 PATCH 时 actions 可显式更新为空数组。"""
    request = SessionPatchRequest.model_validate(
        {
            "actions": [],
        }
    )
    assert request.actions == []


def test_session_create_request_rejects_duplicate_verbs() -> None:
    """验证同一 Session 的 actions 中 verb 必须唯一。"""
    with pytest.raises(ValidationError) as exc_info:
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "description": "demo",
                "max_entities_limit": 100,
                "actions": build_actions_payload() + build_actions_payload(),
            }
        )

    assert any("重复" in error["msg"] or "unique" in error["msg"] for error in exc_info.value.errors())


def test_session_create_request_rejects_legacy_allowed_target_topologies_field() -> None:
    """验证 action schema 不再接受旧字段 allowed_target_topologies。"""
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "description": "demo",
                "max_entities_limit": 100,
                "actions": [
                    {
                        "verb": "social.posted",
                        "description": "post to session board",
                        "allowed_target_topologies": ["board"],
                        "details_schema": {
                            "type": "object",
                            "required": ["content"],
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "minLength": 1,
                                }
                            },
                            "additionalProperties": False,
                        },
                    }
                ],
            }
        )


def test_session_create_request_rejects_target_types_field() -> None:
    """验证 action schema 不再接受 target_types 字段。"""
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "description": "demo",
                "max_entities_limit": 100,
                "actions": [
                    {
                        "verb": "social.posted",
                        "description": "post to session board",
                        "target_types": ["object"],
                        "details_schema": {
                            "type": "object",
                            "required": ["content"],
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "minLength": 1,
                                }
                            },
                            "additionalProperties": False,
                        },
                    }
                ],
            }
        )


def test_session_create_request_rejects_target_constraints_field() -> None:
    """验证 action schema 不再接受 target_constraints 字段。"""
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                "name": "Alpha Session",
                "description": "demo",
                "max_entities_limit": 100,
                "actions": [
                    {
                        "verb": "social.replied",
                        "description": "reply to a post",
                        "target_constraints": {
                            "event": {
                                "verb": ["social.posted"],
                            }
                        },
                        "details_schema": {
                            "type": "object",
                            "required": ["content"],
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "minLength": 1,
                                }
                            },
                            "additionalProperties": False,
                        },
                    }
                ],
            }
        )


def test_session_create_request_rejects_action_parameter_without_description() -> None:
    """验证 details_schema 的参数必须声明 description。"""
    payload = {
        "name": "Alpha Session",
        "description": "demo",
        "max_entities_limit": 100,
        "actions": [
            {
                "verb": "social.posted",
                "description": "post to session board",
                "details_schema": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string",
                            "minLength": 1,
                        }
                    },
                    "additionalProperties": False,
                },
            }
        ],
    }

    with pytest.raises(ValidationError) as exc_info:
        SessionCreateRequest.model_validate(payload)

    assert "description" in str(exc_info.value)


def test_session_create_request_rejects_nested_parameter_without_description() -> None:
    """验证嵌套 object 参数也必须声明 description。"""
    payload = {
        "name": "Alpha Session",
        "description": "demo",
        "max_entities_limit": 100,
        "actions": [
            {
                "verb": "social.posted",
                "description": "post to session board",
                "details_schema": {
                    "type": "object",
                    "required": ["meta"],
                    "properties": {
                        "meta": {
                            "type": "object",
                            "description": "post metadata",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                }
                            },
                            "required": ["topic"],
                            "additionalProperties": False,
                        }
                    },
                    "additionalProperties": False,
                },
            }
        ],
    }

    with pytest.raises(ValidationError) as exc_info:
        SessionCreateRequest.model_validate(payload)

    assert "description" in str(exc_info.value)


def test_session_action_response_from_domain_normalizes_legacy_details_schema() -> None:
    """验证响应序列化兼容历史缺少参数 description 的动作配置。"""
    legacy_action = SessionAction(
        verb="social.posted",
        description="legacy action",
        details_schema={
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {
                    "type": "string",
                    "minLength": 1,
                }
            },
            "additionalProperties": False,
        },
    )

    response_item = SessionActionSchema.from_domain(legacy_action)

    assert response_item.details_schema["properties"]["content"]["description"]
