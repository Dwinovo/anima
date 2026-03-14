from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.responses.entity import EntityContextData


def test_entity_context_response_schema_accepts_context_v2_views() -> None:
    """验证 Context v2 响应结构可通过校验。"""
    payload = {
        "session_id": "session_demo",
        "entity_id": "entity_me",
        "current_world_time": 207,
        "views": {
            "self_recent": {"items": [], "next_cursor": None, "has_more": False},
            "incoming_recent": {"items": [], "next_cursor": None, "has_more": False},
            "neighbor_recent": {"items": [], "next_cursor": None, "has_more": False},
            "global_recent": {"items": [], "next_cursor": None, "has_more": False},
            "hot_targets": {
                "items": [
                    {
                        "target_ref": "board:session_demo",
                        "score": 2.0,
                        "sample_event_ids": ["event_1", "event_2"],
                    }
                ],
                "next_cursor": None,
                "has_more": False,
            },
            "world_snapshot": {
                "online_entities": 1,
                "active_entities": 1,
                "recent_event_count": 7,
            },
        },
    }

    result = EntityContextData.model_validate(payload)

    assert result.views.hot_targets.items[0].target_ref == "board:session_demo"


def test_entity_context_response_schema_rejects_legacy_social_view_fields() -> None:
    """验证旧版社交视图字段不会继续被接受。"""
    payload = {
        "session_id": "session_demo",
        "entity_id": "entity_me",
        "current_world_time": 207,
        "views": {
            "self_recent": {"items": [], "next_cursor": None, "has_more": False},
            "public_feed": {"items": [], "next_cursor": None, "has_more": False},
            "following_feed": {"items": [], "next_cursor": None, "has_more": False},
            "attention": {"items": [], "next_cursor": None, "has_more": False},
            "hot": {"items": [], "next_cursor": None, "has_more": False},
            "world_snapshot": {
                "online_entities": 1,
                "active_entities": 1,
                "recent_event_count": 7,
                "my_following_count": 1,
            },
        },
    }

    with pytest.raises(ValidationError):
        EntityContextData.model_validate(payload)
