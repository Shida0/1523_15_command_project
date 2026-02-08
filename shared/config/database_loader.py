"""
Database configuration loader using the centralized configuration manager.
"""
from sqlalchemy.engine import URL
from shared.config import get_config


def get_async_db_url() -> URL:
    """
    Формирует асинхронный URL для подключения к PostgreSQL.
    Используется SQLAlchemy и Alembic.
    """
    config = get_config()
    return URL.create(
        drivername=f"postgresql+{config.database.async_driver}",
        username=config.database.user,
        password=config.database.password,
        host=config.database.host,
        port=config.database.port,
        database=config.database.db_name
    )


def get_async_dsn() -> str:
    """Возвращает DSN строку в текстовом формате."""
    return str(get_async_db_url())

if __name__ == "__main__":
    print(get_async_dsn())