from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .get_db_config import get_async_db_url


# Создаём асинхронный движок для подключения к PostgreSQL
# Параметр echo=True полезен для отладки - показывает все SQL-запросы
async_engine = create_async_engine(
    url=get_async_db_url(),
    echo=True,  
    pool_pre_ping=True, 
    pool_recycle=3600
)


# Создаём фабрику для асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  
    autocommit=False, 
    autoflush=False
)


# Функция-зависимость для FastAPI, которая будет предоставлять сессию
async def get_async_session():
    """
    Генератор асинхронных сессий для использования в FastAPI роутах.
    Используется с Depends().
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Автокоммит при успешном выполнении
        except Exception:
            await session.rollback()  # Откат при ошибке
            raise
        finally:
            await session.close()


# Функция для закрытия соединения (при завершении приложения)
async def close_async_engine():
    """Корректно закрывает соединение с базой данных."""
    await async_engine.dispose()