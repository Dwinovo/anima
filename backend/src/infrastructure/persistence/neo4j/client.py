from __future__ import annotations

from neo4j import AsyncDriver, AsyncGraphDatabase

from src.infrastructure.persistence.neo4j.cypher import NEO4J_SCHEMA_STATEMENTS


class Neo4jManager:
    """Neo4j 连接管理"""

    def __init__(self, uri: str, user: str, password: str) -> None:
        """初始化对象并注入所需依赖。"""
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
        )

    @property
    def driver(self) -> AsyncDriver:
        """执行 `driver` 相关逻辑。"""
        return self._driver

    async def ensure_schema(self) -> None:
        """确保 Neo4j 关键约束与索引存在。"""
        async with self._driver.session() as session:
            for statement in NEO4J_SCHEMA_STATEMENTS:
                result = await session.run(statement)
                await result.consume()

    async def close(self) -> None:
        """执行 `close` 相关逻辑。"""
        await self._driver.close()
