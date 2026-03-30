import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Pre-import models to ensure SQLAlchemy mappers are configured before tests run
from domains.asteroid.models.asteroid import AsteroidModel
from domains.approach.models.close_approach import CloseApproachModel
from domains.threat.models.threat_assessment import ThreatAssessmentModel


# ============ SESSION FIXTURES ============

@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session fixture."""
    session = AsyncMock(spec=AsyncSession)
    session.add = AsyncMock()
    session.add_all = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.begin = AsyncMock()
    session.connection = Mock()
    session.get = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def mock_session_factory(mock_session):
    """Mock session factory fixture that supports async context manager protocol."""
    # Create a mock that returns an async context manager
    async_context_manager = AsyncMock()
    async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    async_context_manager.__aexit__ = AsyncMock(return_value=None)
    
    factory = Mock(return_value=async_context_manager)
    return factory


@pytest.fixture
def mock_uow(mock_session):
    """Mock Unit of Work fixture."""
    uow = Mock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = mock_session
    
    # Mock repositories
    uow.asteroid_repo = Mock()
    uow.asteroid_repo.session = mock_session
    uow.approach_repo = Mock()
    uow.approach_repo.session = mock_session
    uow.threat_repo = Mock()
    uow.threat_repo.session = mock_session
    
    return uow


# ============ DATABASE FIXTURES ============

@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite engine for integration tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create an async session for integration tests."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def db_session(async_engine):
    """
    Create a database session with tables created.
    For integration tests that need actual database operations.
    """
    # Import all models to ensure tables are created
    from domains.asteroid.models.asteroid import AsteroidModel
    from domains.approach.models.close_approach import CloseApproachModel
    from domains.threat.models.threat_assessment import ThreatAssessmentModel
    
    # Create tables
    async with async_engine.begin() as conn:
        from sqlalchemy.ext.asyncio import AsyncConnection
        from sqlalchemy import MetaData
        metadata = MetaData()
        # Import model metadata
        metadata = AsteroidModel.metadata
        
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
    
    # Cleanup
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


# ============ MODEL FIXTURES ============

@pytest.fixture
def sample_asteroid_data():
    """Sample asteroid data for testing."""
    return {
        "id": 1,
        "designation": "2023 TEST",
        "name": "Test Asteroid",
        "perihelion_au": 0.9,
        "aphelion_au": 1.5,
        "earth_moid_au": 0.03,
        "absolute_magnitude": 20.5,
        "estimated_diameter_km": 0.15,
        "accurate_diameter": False,
        "albedo": 0.15,
        "diameter_source": "calculated",
        "orbit_id": "test_orbit",
        "orbit_class": "Apollo",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_approach_data():
    """Sample approach data for testing."""
    return {
        "id": 1,
        "asteroid_id": 1,
        "approach_time": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        "distance_au": 0.002,
        "distance_km": 299195.74,
        "velocity_km_s": 10.5,
        "asteroid_designation": "2023 TEST",
        "asteroid_name": "Test Asteroid",
        "data_source": "NASA CAD API",
        "calculation_batch_id": "test_batch",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_threat_data():
    """Sample threat data for testing."""
    return {
        "id": 1,
        "asteroid_id": 1,
        "designation": "2023 TEST",
        "fullname": "2023 TEST (Test Asteroid)",
        "ip": 0.001,
        "ts_max": 1,
        "ps_max": -2.5,
        "diameter": 0.15,
        "v_inf": 10.5,
        "h": 20.5,
        "n_imp": 3,
        "impact_years": [2024, 2025, 2026],
        "last_obs": "2023-12-01",
        "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
        "torino_scale_ru": "1 — Нормальный (зелёный)",
        "impact_probability_text_ru": "0.1% (1 к 1,000)",
        "energy_megatons": 10.0,
        "impact_category": "локальный",
        "sentry_last_update": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def invalid_asteroid_data():
    """Invalid asteroid data for testing validation."""
    return {
        "name": "",  # Invalid: empty name
        "designation": "",  # Invalid: empty designation
        "absolute_magnitude": -50,  # Invalid: too low magnitude
        "estimated_diameter_km": -1,  # Invalid: negative diameter
        "albedo": 1.5  # Invalid: albedo > 1
    }


# ============ HELPER FIXTURES ============

@pytest.fixture
def mock_scalar_result():
    """
    Helper fixture to create a mock scalar result.
    Useful for mocking SQLAlchemy query results.
    """
    def _create_scalar_result(value):
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=value)
        return mock_result
    
    return _create_scalar_result


@pytest.fixture
def mock_execute_result():
    """
    Helper fixture to create a mock execute result.
    Useful for mocking session.execute() returns.
    """
    def _create_execute_result(scalar_value):
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=scalar_value)
        mock_result.scalar_one_or_none = Mock(return_value=scalar_value)
        mock_result.scalars = Mock(return_value=[])
        return mock_result
    
    return _create_execute_result


@pytest.fixture
def ordered_scalar_mock():
    """
    Helper fixture to create an ordered scalar mock.
    Returns values in sequence, then the last value repeatedly.
    This avoids fragile order-dependent tests.
    """
    def _create_ordered_mock(values, default=0):
        values_list = list(values)
        call_count = [0]
        
        def scalar_side_effect():
            idx = min(call_count[0], len(values_list) - 1)
            call_count[0] += 1
            return values_list[idx] if idx < len(values_list) else default
        
        mock_result = Mock()
        mock_result.scalar = Mock(side_effect=scalar_side_effect)
        return mock_result
    
    return _create_ordered_mock


# ============ API TEST FIXTURES ============

@pytest.fixture
def mock_asteroid_service(mock_session_factory):
    """Mock asteroid service for API tests."""
    from domains.asteroid.services.asteroid_service import AsteroidService
    service = AsteroidService(mock_session_factory)
    return service


@pytest.fixture
def mock_approach_service(mock_session_factory):
    """Mock approach service for API tests."""
    from domains.approach.services.approach_service import ApproachService
    service = ApproachService(mock_session_factory)
    return service


@pytest.fixture
def mock_threat_service(mock_session_factory):
    """Mock threat service for API tests."""
    from domains.threat.services.threat_service import ThreatService
    service = ThreatService(mock_session_factory)
    return service


# ============ UTILITY FIXTURES ============

@pytest.fixture
def create_mock_model():
    """
    Factory fixture to create mock model instances.
    Avoids using SimpleNamespace and provides proper mock structure.
    """
    def _create_mock(model_class, data_dict):
        mock_model = Mock(spec=model_class)
        mock_model.__table__ = Mock()
        mock_model.__table__.columns = []
        
        for key, value in data_dict.items():
            setattr(mock_model, key, value)
            mock_col = Mock()
            mock_col.name = key
            mock_model.__table__.columns.append(mock_col)
        
        return mock_model
    
    return _create_mock