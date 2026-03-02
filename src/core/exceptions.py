from __future__ import annotations

from typing import Any


class AnimaException(Exception):
    """Base exception for service-layer business errors."""

    def __init__(
        self,
        *,
        status_code: int,
        code: int,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class SessionNotFoundException(AnimaException):
    def __init__(self, session_id: str) -> None:
        """初始化对象并注入所需依赖。"""
        super().__init__(
            status_code=404,
            code=40401,
            message=f"Session {session_id} does not exist.",
        )


class QuotaExceededException(AnimaException):
    def __init__(self, session_id: str, limit: int) -> None:
        """初始化对象并注入所需依赖。"""
        super().__init__(
            status_code=403,
            code=40301,
            message=f"Session {session_id} has reached max_agents_limit ({limit}).",
        )


class AgentNotFoundException(AnimaException):
    def __init__(self, session_id: str, uuid: str) -> None:
        """初始化对象并注入所需依赖。"""
        super().__init__(
            status_code=404,
            code=40402,
            message=f"Agent {uuid} not found in session {session_id}.",
        )


class DisplayNameAllocationException(AnimaException):
    def __init__(self, session_id: str, name: str) -> None:
        """初始化对象并注入所需依赖。"""
        super().__init__(
            status_code=409,
            code=40901,
            message=f"Unable to allocate display name for '{name}' in session {session_id}.",
        )
