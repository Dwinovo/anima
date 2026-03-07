from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.requests.event import EventListQuery


def test_event_list_query_accepts_valid_cursor() -> None:
    """验证合法游标可通过校验并正确解析。"""
    query = EventListQuery.model_validate(
        {
            "limit": 30,
            "cursor": "12004:event_abc123",
        }
    )

    world_time, event_id = query.parse_cursor()
    assert query.limit == 30
    assert world_time == 12004
    assert event_id == "event_abc123"


def test_event_list_query_accepts_valid_verb_domain() -> None:
    """验证合法动词域可通过校验。"""
    query = EventListQuery.model_validate({"verb_domain": "social"})

    assert query.verb_domain == "social"


@pytest.mark.parametrize("invalid_verb_domain", ["social.posted", "Social", "social-", ""])
def test_event_list_query_rejects_invalid_verb_domain(invalid_verb_domain: str) -> None:
    """验证非法动词域会触发校验错误。"""
    with pytest.raises(ValidationError) as exc_info:
        EventListQuery.model_validate({"verb_domain": invalid_verb_domain})

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("verb_domain",) for error in errors)


def test_event_list_query_rejects_invalid_cursor_format() -> None:
    """验证非法游标格式会触发校验错误。"""
    with pytest.raises(ValidationError) as exc_info:
        EventListQuery.model_validate({"cursor": "bad-cursor-format"})

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("cursor",) for error in errors)
