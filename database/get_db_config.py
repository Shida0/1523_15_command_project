from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine
from decouple import config


def get_async_db_url() -> URL:
    """
    Формирует асинхронный URL для подключения к PostgreSQL.
    Используется SQLAlchemy и Alembic.
    """
    return URL.create(
        drivername=f"postgresql+{config('POSTGRES_ASYNC_DRIVER', default='asyncpg')}",
        username=config('POSTGRES_USER'),
        password=config('POSTGRES_PASSWORD'),
        host=config('POSTGRES_HOST', default='localhost'),
        port=config('POSTGRES_PORT', default=5432, cast=int),
        database=config('POSTGRES_DB')
    )


# Для удобства можно также создать строку подключения в виде текста
def get_async_dsn() -> str:
    """Возвращает DSN строку в текстовом формате."""
    return str(get_async_db_url())


# Пример использования (можно импортировать в других модулях)
if __name__ == "__main__":
    print("DSN для подключения:", get_async_dsn())