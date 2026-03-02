from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for infrastructure clients."""

    # --------------------------------------------
    # PostgreSQL
    # --------------------------------------------
    database_url: str

    # --------------------------------------------
    # Redis
    # --------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # --------------------------------------------
    # MongoDB
    # --------------------------------------------
    mongo_url: str = "mongodb://localhost:27017"
    mongo_database: str = "anima"

    # --------------------------------------------
    # Neo4j
    # --------------------------------------------
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # --------------------------------------------
    # OpenAI / LLM
    # --------------------------------------------
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    default_llm_model: str = "gpt-4o"

    # --------------------------------------------
    # LangGraph
    # --------------------------------------------
    langgraph_checkpoint_ttl_seconds: int = 7200
    langgraph_working_memory_window: int = 3
    langgraph_checkpoint_namespace: str = "agent_decision"

    # --------------------------------------------
    # CORS
    # --------------------------------------------
    cors_allow_origins: str = "*"
    cors_allow_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allow_headers: str = "*"
    cors_allow_credentials: bool = False

    @staticmethod
    def _parse_csv_values(value: str) -> list[str]:
        """解析逗号分隔配置并返回去重前的有序列表。"""
        normalized = value.strip()
        if not normalized:
            return []
        if normalized == "*":
            return ["*"]
        return [item.strip() for item in normalized.split(",") if item.strip()]

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """返回 CORS 允许的来源列表。"""
        parsed = self._parse_csv_values(self.cors_allow_origins)
        return parsed or ["*"]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        """返回 CORS 允许的 HTTP 方法列表。"""
        parsed = self._parse_csv_values(self.cors_allow_methods)
        return parsed or ["*"]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        """返回 CORS 允许的请求头列表。"""
        parsed = self._parse_csv_values(self.cors_allow_headers)
        return parsed or ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
