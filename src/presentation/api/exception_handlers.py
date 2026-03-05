from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from src.core.exceptions import AnimaException
from src.presentation.api.schemas.responses.envelope import ApiResponse

logger = logging.getLogger(__name__)


def _to_json_safe(value: Any) -> Any:
    """将任意对象转换为可 JSON 序列化结构。"""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    return str(value)


def _json_response(*, http_status: int, code: int, message: str, data: Any | None = None) -> JSONResponse:
    """构建统一格式的 JSON 响应。"""
    payload = ApiResponse(code=code, message=message, data=data).model_dump()
    return JSONResponse(status_code=http_status, content=payload)


async def request_validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # 400 - request body/query/path validation errors
    """执行 `request_validation_exception_handler` 相关逻辑。"""
    details = {"errors": _to_json_safe(exc.errors())}
    return _json_response(
        http_status=status.HTTP_400_BAD_REQUEST,
        code=status.HTTP_400_BAD_REQUEST,
        message="Validation error.",
        data=details,
    )


async def anima_exception_handler(_: Request, exc: AnimaException) -> JSONResponse:
    """执行 `anima_exception_handler` 相关逻辑。"""
    return _json_response(
        http_status=exc.status_code,
        code=exc.code,
        message=exc.message,
        data=exc.details,
    )


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """处理未被显式捕获的异常并返回统一错误响应。"""
    logger.exception("Unhandled exception", exc_info=exc)

    return _json_response(
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal server error.",
        data=None,
    )
