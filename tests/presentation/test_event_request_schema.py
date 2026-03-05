from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.requests.event import EventReportRequest


def test_event_report_request_accepts_domain_verb() -> None:
    """验证合法 domain.verb 可通过上报请求校验。"""
    payload = EventReportRequest.model_validate(
        {
            "world_time": 12006,
            "subject_uuid": "entity_a",
            "verb": "social.posted",
            "target_ref": "board:session_demo",
            "details": {"content": "hello"},
            "schema_version": 1,
        }
    )

    assert payload.verb == "social.posted"


@pytest.mark.parametrize(
    "invalid_verb",
    [
        "POSTED",
        "social-posted",
        "social.",
        ".posted",
    ],
)
def test_event_report_request_rejects_invalid_verb_format(invalid_verb: str) -> None:
    """验证不符合 domain.verb 的动作字符串会被拒绝。"""
    with pytest.raises(ValidationError) as exc_info:
        EventReportRequest.model_validate(
            {
                "world_time": 12006,
                "subject_uuid": "entity_a",
                "verb": invalid_verb,
                "target_ref": "board:session_demo",
                "details": {},
                "schema_version": 1,
            }
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("verb",) for error in errors)
