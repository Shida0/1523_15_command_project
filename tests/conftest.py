import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from decimal import Decimal

# Pre-import models to ensure SQLAlchemy mappers are configured before tests run
from domains.asteroid.models.asteroid import AsteroidModel
from domains.approach.models.close_approach import CloseApproachModel
from domains.threat.models.threat_assessment import ThreatAssessmentModel


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session fixture."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = Mock()
    session.flush = AsyncMock()
    session.begin = AsyncMock()
    return session


@pytest.fixture
def mock_session_factory(mock_session):
    """Mock session factory fixture."""
    factory = Mock(return_value=mock_session)
    return factory


@pytest.fixture
def mock_uow(mock_session):
    """Mock Unit of Work fixture."""
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = mock_session
    return uow


@pytest.fixture
def sample_asteroid_data():
    """Sample asteroid data for testing."""
    return {
        "id": 1,
        "name": "Test Asteroid",
        "designation": "2023 TEST",
        "absolute_magnitude": 20.5,
        "estimated_diameter_min_km": 0.1,
        "estimated_diameter_max_km": 0.3,
        "albedo": 0.15,
        "is_hazardous": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_approach_data():
    """Sample approach data for testing."""
    return {
        "id": 1,
        "asteroid_id": 1,
        "approach_date": datetime.now().date(),
        "distance_km": 100000.0,
        "velocity_km_s": 10.5,
        "orbit_class": "AMO",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_threat_data():
    """Sample threat data for testing."""
    return {
        "id": 1,
        "asteroid_id": 1,
        "palermo_scale": Decimal("0.5"),
        "torino_scale": 1,
        "impact_probability": Decimal("0.001"),
        "potential_energy_mt": Decimal("100.0"),
        "is_hazardous": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def invalid_asteroid_data():
    """Invalid asteroid data for testing validation."""
    return {
        "name": "",  # Invalid: empty name
        "designation": "",  # Invalid: empty designation
        "absolute_magnitude": -50,  # Invalid: too low magnitude
        "estimated_diameter_min_km": -1,  # Invalid: negative diameter
        "albedo": 1.5  # Invalid: albedo > 1
    }