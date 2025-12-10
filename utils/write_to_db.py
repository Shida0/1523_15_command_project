from controllers import AsteroidController
from models.engine import AsyncSessionLocal
from .get_data import get_neo
import asyncio


async def async_write_data():
    data = get_neo()
    # Используем фабрику асинхронных сессий напрямую 
    async with AsyncSessionLocal() as session:
        await AsteroidController().bulk_create(session, data)
        # bulk_create уже делает commit, но оставим явное закрытие контекста через async with


def write_data():
    asyncio.run(async_write_data())