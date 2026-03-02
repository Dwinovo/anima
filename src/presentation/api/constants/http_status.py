from __future__ import annotations

from starlette import status

# ============================================================
# Success
# ============================================================

HTTP_200_OK = status.HTTP_200_OK
HTTP_201_CREATED = status.HTTP_201_CREATED
HTTP_202_ACCEPTED = status.HTTP_202_ACCEPTED
HTTP_204_NO_CONTENT = status.HTTP_204_NO_CONTENT


# ============================================================
# Client Errors
# ============================================================

HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_409_CONFLICT = status.HTTP_409_CONFLICT
HTTP_422_UNPROCESSABLE_CONTENT = status.HTTP_422_UNPROCESSABLE_CONTENT
# Backward-compatible alias.
HTTP_422_UNPROCESSABLE_ENTITY = HTTP_422_UNPROCESSABLE_CONTENT


# ============================================================
# Server Errors
# ============================================================

HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
HTTP_503_SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE


# ============================================================
# Semantic Aliases (推荐在业务中使用这些)
# ============================================================

# Session
SESSION_CREATED = HTTP_201_CREATED
SESSION_DELETED = HTTP_204_NO_CONTENT

# Agent
AGENT_REGISTERED = HTTP_201_CREATED
AGENT_REMOVED = HTTP_204_NO_CONTENT

# Event
EVENT_ACCEPTED = HTTP_202_ACCEPTED

# Memory
MEMORY_RETRIEVED = HTTP_200_OK


# ============================================================
# Default Error Mapping (可供异常处理器使用)
# ============================================================

DEFAULT_ERROR_STATUS = HTTP_500_INTERNAL_SERVER_ERROR
VALIDATION_ERROR_STATUS = HTTP_400_BAD_REQUEST
NOT_FOUND_STATUS = HTTP_404_NOT_FOUND
CONFLICT_STATUS = HTTP_409_CONFLICT
