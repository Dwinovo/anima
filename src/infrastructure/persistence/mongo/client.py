from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoManager:
    """Mongo 连接管理：统一创建 client、提供 database、负责关闭。"""

    def __init__(self, mongo_url: str, db_name: str) -> None:
        """初始化对象并注入所需依赖。"""
        self._client = AsyncIOMotorClient(mongo_url)
        self._db: AsyncIOMotorDatabase = self._client[db_name]

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """执行 `db` 相关逻辑。"""
        return self._db

    async def close(self) -> None:
        # motor 的 client 关闭是同步方法
        """执行 `close` 相关逻辑。"""
        self._client.close()