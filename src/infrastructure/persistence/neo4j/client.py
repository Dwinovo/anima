from __future__ import annotations

from neo4j import AsyncDriver, AsyncGraphDatabase


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

    async def close(self) -> None:
        """执行 `close` 相关逻辑。"""
        await self._driver.close()