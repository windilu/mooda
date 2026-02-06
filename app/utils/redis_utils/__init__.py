
from typing import Optional
from typing import AsyncIterator
from redis.asyncio import from_url, Redis


async def init_redis_pool(host: str, password: str = "", db: int = 0, port: int = 6379) -> AsyncIterator[Redis]:
    session = await from_url(
        url=f"redis://{host}",
        port=port,
        password=password,
        db=db,
        encoding="utf-8",
        decode_responses=True
    )
    return session



class RedisClient:
    """全局 Redis 客户端管理器"""
    client: Optional[Redis] = None

    @classmethod
    async def initialize(cls, **kwargs):
        """在 lifespan 中调用初始化"""
        cls.client = await init_redis_pool(**kwargs)

    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls.client:
            await cls.client.close()
            cls.client = None

    @classmethod
    def get_client(cls) -> Redis:
        """在任何地方获取 Redis 客户端"""
        if cls.client is None:
            raise RuntimeError("Redis 未初始化，请先调用 initialize()")
        return cls.client


# 创建全局实例
redis_client = RedisClient()