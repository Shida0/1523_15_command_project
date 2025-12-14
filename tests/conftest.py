"""
Общие фикстуры и настройки для тестов.
"""
import asyncio
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from models.base import Base
from models.asteroid import AsteroidModel
from models.close_approach import CloseApproachModel
from models.engine import AsyncSessionLocal
from models.threat_assessment import ThreatAssessmentModel

# Настройка логирования для тестов
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

@pytest.fixture(autouse=True)
async def cleanup_before_test(async_session):
    """Автоматически очищает БД перед каждым тестом."""
    await clean_database(async_session)
    await async_session.commit()

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def async_engine():
    """Создание асинхронного движка для тестовой БД."""
    # Используем существующую БД, но будем работать в транзакциях
    from models.engine import async_engine as existing_engine
    # Создаем отдельную сессию для тестов
    test_engine = existing_engine
    
    # Проверяем соединение
    async with test_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    
    yield test_engine
    
    await test_engine.dispose()
    
@pytest.fixture(scope="function")
async def async_session():
    """Создаёт новую сессию для каждого теста и очищает БД после."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Очищаем все таблицы после теста
            await clean_database(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            
async def clean_database(session: AsyncSession):
    """Очищает все таблицы базы данных."""
    await session.execute(text("TRUNCATE TABLE threat_assessment_models CASCADE"))
    await session.execute(text("TRUNCATE TABLE close_approach_models CASCADE"))
    await session.execute(text("TRUNCATE TABLE asteroid_models CASCADE"))
    await session.commit()

@pytest.fixture(scope="session")
def event_loop():
    """Создаёт event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_asteroid_data():
    """Фикстура с тестовыми данными астероида."""
    return {
        "mpc_number": 999999,  # Несуществующий номер для тестов
        "name": "Test Asteroid",
        "designation": "2024 TE1",
        "perihelion_au": 0.95,
        "aphelion_au": 1.78,
        "earth_moid_au": 0.05,
        "absolute_magnitude": 18.5,
        "estimated_diameter_km": 0.3,
        "accurate_diameter": True,
        "albedo": 0.25,
        "is_neo": True,
        "is_pha": True
    }

@pytest.fixture
async def test_asteroid(async_session, sample_asteroid_data):
    """Создание тестового астероида в БД."""
    asteroid = AsteroidModel(**sample_asteroid_data)
    async_session.add(asteroid)
    await async_session.flush()
    await async_session.refresh(asteroid)
    return asteroid

@pytest.fixture
async def test_close_approach(async_session, test_asteroid):
    """Создание тестового сближения в БД."""
    approach = CloseApproachModel(
        asteroid_id=test_asteroid.id,
        approach_time=datetime.now() + timedelta(days=30),
        distance_au=0.02,
        velocity_km_s=18.5,
        calculation_batch_id="test_batch_001"
    )
    async_session.add(approach)
    await async_session.flush()
    await async_session.refresh(approach)
    return approach

@pytest.fixture
async def test_threat_assessment(async_session, test_close_approach):
    """Создание тестовой оценки угрозы в БД."""
    threat = ThreatAssessmentModel(
        approach_id=test_close_approach.id,
        threat_level="высокий",
        impact_category="региональный",
        energy_megatons=10.5
    )
    async_session.add(threat)
    await async_session.flush()
    await async_session.refresh(threat)
    return threat

@pytest.fixture
def mock_async_session():
    """Мок асинхронной сессии для тестов без БД."""
    session = MagicMock(spec=AsyncSession)
    
    # Синхронные методы
    session.add = MagicMock()
    session.delete = MagicMock()
    
    # Асинхронные методы должны быть настроены как асинхронные
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.rollback = AsyncMock() 
    
    # Настроить результат execute
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=None)
    mock_result.scalars = AsyncMock(return_value=AsyncMock(all=AsyncMock(return_value=[])))
    session.execute.return_value = mock_result
    
    return session

@pytest.fixture(autouse=True)
async def cleanup_test_data(async_session):
    """Автоматическая очистка тестовых данных после каждого теста.
    
    Удаляет записи, созданные во время тестов (по определенным критериям).
    """
    yield
    
    # Удаляем тестовые записи по маркерам (например, mpc_number = 999999)
    try:
        await async_session.execute(
            text("DELETE FROM asteroid_models WHERE mpc_number = 999999")
        )
        await async_session.execute(
            text("DELETE FROM close_approach_models WHERE calculation_batch_id LIKE 'test_%'")
        )
        await async_session.commit()
    except Exception as e:
        await async_session.rollback()
        logging.warning(f"Ошибка при очистке тестовых данных: {e}")

# Регистрация маркеров
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark test as slow (skip with -m 'not slow')"
    )
    config.addinivalue_line(
        "markers", "external_api: mark test as using external API"
    )
    config.addinivalue_line(
        "markers", "db: mark test as requiring database"
    )