from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

from src.core.config import Settings, settings
from src.main import app


def test_settings_can_parse_cors_csv_values() -> None:
    """验证 CORS 配置可从逗号分隔字符串解析为列表。"""
    cfg = Settings(
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/anima",
        neo4j_uri="bolt://127.0.0.1:7687",
        neo4j_user="neo4j",
        neo4j_password="pass",
        cors_allow_origins="https://a.example.com, https://b.example.com",
        cors_allow_methods="GET,POST",
        cors_allow_headers="Authorization,Content-Type",
        cors_allow_credentials=True,
    )

    assert cfg.cors_allow_origins_list == ["https://a.example.com", "https://b.example.com"]
    assert cfg.cors_allow_methods_list == ["GET", "POST"]
    assert cfg.cors_allow_headers_list == ["Authorization", "Content-Type"]
    assert cfg.cors_allow_credentials is True


def test_app_registers_cors_middleware() -> None:
    """验证 FastAPI 应用已注册 CORS 中间件。"""
    cors_middlewares = [middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware]

    assert len(cors_middlewares) == 1
    cors = cors_middlewares[0]
    assert cors.kwargs["allow_origins"] == settings.cors_allow_origins_list
    assert cors.kwargs["allow_methods"] == settings.cors_allow_methods_list
    assert cors.kwargs["allow_headers"] == settings.cors_allow_headers_list
    assert cors.kwargs["allow_credentials"] == settings.cors_allow_credentials
