from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from shared.config import get_config
import logging

logger = logging.getLogger(__name__)

config = get_config()

async_engine = create_async_engine(
    url=config.get_database_url(),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI - предоставляет сессию без автокомита.
    Контроллеры сами управляют коммитами.
    """
    session = AsyncSessionLocal()
    try:
        logger.debug("Сессия БД открыта (зависимость FastAPI)")
        yield session

    except Exception as e:
        logger.error(f"Ошибка в сессии БД: {e}")
        raise
    finally:
        await session.close()
        logger.debug("Сессия БД закрыта (зависимость FastAPI)")

async def close_async_engine():
   """Корректно закрывает соединение с базой данных."""
   await async_engine.dispose()