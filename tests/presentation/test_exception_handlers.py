from __future__ import annotations

import json

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from src.core.exceptions import SessionNotFoundException
from src.presentation.api.exception_handlers import (
    anima_exception_handler,
    request_validation_exception_handler,
)


def _build_request() -> Request:
    """执行 `_build_request` 相关逻辑。"""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_anima_exception_handler_returns_domain_status_and_code() -> None:
    """验证该测试场景的预期行为。"""
    request = _build_request()
    exc = SessionNotFoundException("session_missing")

    response = await anima_exception_handler(request, exc)
    payload = json.loads(response.body)

    assert response.status_code == 404
    assert payload["code"] == 40401
    assert payload["message"] == "Session session_missing does not exist."
    assert payload["data"] is None


@pytest.mark.asyncio
async def test_request_validation_exception_handler_returns_400() -> None:
    """验证参数校验失败会返回 400。"""
    request = _build_request()
    exc = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("body", "name"),
                "msg": "Field required",
                "input": None,
            }
        ]
    )

    response = await request_validation_exception_handler(request, exc)
    payload = json.loads(response.body)

    assert response.status_code == 400
    assert payload["code"] == 400
    assert payload["message"] == "Validation error."
    assert payload["data"] is not None
