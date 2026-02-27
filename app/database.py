from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    print("✅ MongoDB connected")


async def close_db():
    global client
    if client:
        client.close()
        print("❌ MongoDB disconnected")


def get_db():
    return client[settings.db_name]
