from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope.

    All HTTP responses must follow:

    {
        "code": int,
        "message": str,
        "data": T | None
    }
    """

    code: int
    message: str
    data: T | None = None

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class SuccessResponse(ApiResponse[T]):
    """Semantic alias for successful responses."""


class ErrorResponse(ApiResponse[None]):
    """Semantic alias for error responses (data is always None)."""


__all__ = ["ApiResponse", "SuccessResponse", "ErrorResponse"]
