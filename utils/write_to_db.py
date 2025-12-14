from controllers import AsteroidController
from models.engine import AsyncSessionLocal
from .get_data import get_neo
import asyncio

async def async_write_data():
    try:
        data = get_neo()
        async with AsyncSessionLocal() as session:
            await AsteroidController().bulk_create(session, data)
    except Exception as e:
        # Логирование ошибки
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при записи данных: {e}")
        raise

def write_data():
    asyncio.run(async_write_data())