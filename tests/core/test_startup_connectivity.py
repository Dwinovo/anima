from __future__ import annotations

import logging

import pytest

from src.main import _run_startup_dependency_checks


class _HealthyRedis:
    async def ping(self) -> bool:
        return True


class _UnhealthyRedis:
    async def ping(self) -> bool:
        raise RuntimeError("redis unavailable")


class _HealthyMongo:
    async def ping(self) -> bool:
        return True


class _HealthyNeo4j:
    async def ensure_schema(self) -> None:
        return None


class _HealthyPgConnection:
    async def execute(self, _statement: object) -> None:
        return None


class _HealthyPgConnectContext:
    async def __aenter__(self) -> _HealthyPgConnection:
        return _HealthyPgConnection()

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False


class _HealthyPgEngine:
    def connect(self) -> _HealthyPgConnectContext:
        return _HealthyPgConnectContext()


@pytest.mark.asyncio
async def test_startup_dependency_checks_pass_when_all_backends_are_healthy() -> None:
    results = await _run_startup_dependency_checks(
        redis=_HealthyRedis(),
        mongo=_HealthyMongo(),
        pg_engine=_HealthyPgEngine(),
        neo4j=_HealthyNeo4j(),
    )

    assert results == {
        "redis": True,
        "mongo": True,
        "postgres": True,
        "neo4j": True,
    }


@pytest.mark.asyncio
async def test_startup_dependency_checks_report_errors_without_raising(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR)

    results = await _run_startup_dependency_checks(
        redis=_UnhealthyRedis(),
        mongo=_HealthyMongo(),
        pg_engine=_HealthyPgEngine(),
        neo4j=_HealthyNeo4j(),
    )

    assert results["redis"] is False
    assert "service will continue running" in caplog.text.lower()
