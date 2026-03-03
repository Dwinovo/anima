from __future__ import annotations

from redis.asyncio import Redis


class RedisClient:
    """Redis 客户端封装：统一连接管理并暴露原子数据操作。"""

    def __init__(self, redis: Redis) -> None:
        """初始化 Redis 客户端封装。

        Args:
            redis: 已建立的异步 Redis 连接对象。
        """
        self._redis = redis

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisClient":
        """根据 Redis URL 创建客户端实例。

        Args:
            redis_url: Redis 连接地址，例如 ``redis://localhost:6379/0``。

        Returns:
            RedisClient: 封装后的 Redis 客户端实例。
        """
        redis = Redis.from_url(redis_url, decode_responses=True)
        return cls(redis)

    async def close(self) -> None:
        """关闭 Redis 连接并释放底层资源。"""
        await self._redis.aclose()

    async def set_value(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """以原子方式写入字符串键值，可选设置过期时间。"""
        if ttl_seconds is None:
            await self._redis.set(key, value)
            return
        await self._redis.set(key, value, ex=ttl_seconds)

    async def set_value_if_absent(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        """仅当键不存在时写入值，返回是否写入成功。"""
        kwargs: dict[str, int] = {}
        if ttl_seconds is not None:
            kwargs["ex"] = ttl_seconds
        result = await self._redis.set(key, value, nx=True, **kwargs)
        return bool(result)

    async def get_value(self, key: str) -> str | None:
        """读取字符串键值，不存在时返回 ``None``。"""
        value = await self._redis.get(key)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    async def delete_key(self, key: str) -> int:
        """删除指定键并返回删除数量。"""
        return int(await self._redis.delete(key))

    async def add_set_member(self, key: str, member: str) -> int:
        """向 Set 集合添加成员并返回新增数量。"""
        return int(await self._redis.sadd(key, member))

    async def remove_set_member(self, key: str, member: str) -> int:
        """从 Set 集合移除成员并返回移除数量。"""
        return int(await self._redis.srem(key, member))

    async def is_set_member(self, key: str, member: str) -> bool:
        """判断成员是否存在于指定 Set 集合。"""
        return bool(await self._redis.sismember(key, member))

    async def get_set_size(self, key: str) -> int:
        """获取 Set 集合成员总数。"""
        return int(await self._redis.scard(key))

    async def get_set_members(self, key: str) -> list[str]:
        """获取 Set 集合全部成员，并按字典序稳定返回。"""
        members = await self._redis.smembers(key)
        normalized = [member.decode("utf-8") if isinstance(member, bytes) else str(member) for member in members]
        return sorted(normalized)

    async def incr_value(self, key: str) -> int:
        """将字符串计数器自增并返回最新值。"""
        return int(await self._redis.incr(key))

    async def get_hash_fields(self, key: str, fields: list[str]) -> dict[str, str]:
        """批量读取 Hash 字段并返回存在值的映射。"""
        if not fields:
            return {}
        values = await self._redis.hmget(key, fields)
        result: dict[str, str] = {}
        for field, value in zip(fields, values, strict=True):
            if value is None:
                continue
            if isinstance(value, bytes):
                result[field] = value.decode("utf-8")
            else:
                result[field] = str(value)
        return result

    async def set_hash_field(self, key: str, field: str, value: str) -> None:
        """写入 Hash 单字段值。"""
        await self._redis.hset(key, field, value)
