from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config import settings

_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> AsyncIOMotorDatabase:
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client[settings.mongodb_db_name]


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
