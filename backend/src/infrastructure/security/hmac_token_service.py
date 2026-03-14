from __future__ import annotations

import base64
import hmac
import json
from hashlib import sha256
from time import time
from uuid import uuid4

from src.core.exceptions import AuthenticationFailedException
from src.domain.entity.token_service import TokenClaims


class HmacTokenService:
    """基于 HMAC-SHA256 的轻量 token 服务。"""

    _ACCESS_TOKEN_TYPE = "access"
    _REFRESH_TOKEN_TYPE = "refresh"

    def __init__(
        self,
        *,
        secret: str,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._secret = secret.encode("utf-8")
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.refresh_token_ttl_seconds = refresh_token_ttl_seconds

    async def issue_access_token(
        self,
        *,
        session_id: str,
        entity_id: str,
        token_version: int,
    ) -> str:
        """签发 access token。"""
        now = int(time())
        payload = {
            "typ": self._ACCESS_TOKEN_TYPE,
            "sid": session_id,
            "eid": entity_id,
            "ver": token_version,
            "iat": now,
            "exp": now + self.access_token_ttl_seconds,
        }
        return self._encode(payload=payload)

    async def issue_refresh_token(
        self,
        *,
        session_id: str,
        entity_id: str,
        token_version: int,
        refresh_jti: str,
    ) -> str:
        """签发 refresh token。"""
        now = int(time())
        payload = {
            "typ": self._REFRESH_TOKEN_TYPE,
            "sid": session_id,
            "eid": entity_id,
            "ver": token_version,
            "jti": refresh_jti,
            "iat": now,
            "exp": now + self.refresh_token_ttl_seconds,
        }
        return self._encode(payload=payload)

    async def parse_token(self, *, token: str) -> TokenClaims:
        """解析并校验 token。"""
        header_part, payload_part, signature_part = self._split_token(token)
        signing_input = f"{header_part}.{payload_part}".encode("utf-8")
        expected_signature = self._sign(signing_input)
        provided_signature = self._b64decode(signature_part)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise AuthenticationFailedException("Invalid token signature.")

        payload = self._json_loads(payload_part)
        token_type = payload.get("typ")
        session_id = payload.get("sid")
        entity_id = payload.get("eid")
        token_version = payload.get("ver")
        expires_at = payload.get("exp")
        refresh_jti = payload.get("jti")

        if token_type not in {self._ACCESS_TOKEN_TYPE, self._REFRESH_TOKEN_TYPE}:
            raise AuthenticationFailedException("Invalid token type.")
        if not isinstance(session_id, str) or not session_id:
            raise AuthenticationFailedException("Invalid session in token.")
        if not isinstance(entity_id, str) or not entity_id:
            raise AuthenticationFailedException("Invalid entity in token.")
        if not isinstance(token_version, int) or token_version <= 0:
            raise AuthenticationFailedException("Invalid token version.")
        if not isinstance(expires_at, int):
            raise AuthenticationFailedException("Invalid token expiration.")
        if expires_at < int(time()):
            raise AuthenticationFailedException("Token expired.")
        if token_type == self._REFRESH_TOKEN_TYPE and (not isinstance(refresh_jti, str) or not refresh_jti):
            raise AuthenticationFailedException("Invalid refresh token jti.")

        return TokenClaims(
            token_type=token_type,
            session_id=session_id,
            entity_id=entity_id,
            token_version=token_version,
            expires_at=expires_at,
            refresh_jti=refresh_jti if isinstance(refresh_jti, str) else None,
        )

    async def generate_refresh_jti(self) -> str:
        """生成 refresh_jti。"""
        return uuid4().hex

    @staticmethod
    def _split_token(token: str) -> tuple[str, str, str]:
        """拆分 token 三段并校验基本格式。"""
        parts = token.split(".")
        if len(parts) != 3:
            raise AuthenticationFailedException("Malformed token.")
        return parts[0], parts[1], parts[2]

    @staticmethod
    def _json_loads(payload_part: str) -> dict[str, object]:
        """解析 payload JSON。"""
        try:
            payload_bytes = HmacTokenService._b64decode(payload_part)
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise AuthenticationFailedException("Malformed token payload.") from exc
        if not isinstance(payload, dict):
            raise AuthenticationFailedException("Malformed token payload.")
        return payload

    def _encode(self, *, payload: dict[str, object]) -> str:
        """编码 payload 为签名 token。"""
        header = {"alg": "HS256", "typ": "JWT"}
        header_part = self._b64encode(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
        payload_part = self._b64encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
        signing_input = f"{header_part}.{payload_part}".encode("utf-8")
        signature_part = self._b64encode(self._sign(signing_input))
        return f"{header_part}.{payload_part}.{signature_part}"

    def _sign(self, signing_input: bytes) -> bytes:
        """对签名输入执行 HMAC-SHA256。"""
        return hmac.new(self._secret, signing_input, sha256).digest()

    @staticmethod
    def _b64encode(raw: bytes) -> str:
        """Base64 URL-safe 编码并去掉 padding。"""
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64decode(raw: str) -> bytes:
        """Base64 URL-safe 解码并自动补齐 padding。"""
        padded = raw + "=" * (-len(raw) % 4)
        return base64.urlsafe_b64decode(padded.encode("utf-8"))
