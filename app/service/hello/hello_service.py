from fastapi import APIRouter

from app.utils.redis_utils import redis_client


async def hello_service():
    value = await redis_client.get_client().get("rags")
    print(value)
    return {"message": "Hello World"}