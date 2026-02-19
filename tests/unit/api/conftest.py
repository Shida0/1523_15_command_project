"""
Pytest fixtures for API unit tests.

This module provides mock services and test client for isolating API tests
from the database and real service implementations.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path to enable imports
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from main import app
from api.dependencies import get_asteroid_service, get_approach_service, get_threat_service


@pytest.fixture(scope="function")
def mock_asteroid_service():
    """Create a mock asteroid service with AsyncMock methods."""
    service = Mock()
    service.get_by_moid = AsyncMock(return_value=[])
    service.get_by_orbit_class = AsyncMock(return_value=[])
    service.get_with_accurate_diameter = AsyncMock(return_value=[])
    service.get_statistics = AsyncMock(return_value={})
    service.get_by_designation = AsyncMock(return_value=None)
    return service


@pytest.fixture(scope="function")
def mock_approach_service():
    """Create a mock approach service with AsyncMock methods."""
    service = Mock()
    service.get_upcoming = AsyncMock(return_value=[])
    service.get_closest = AsyncMock(return_value=[])
    service.get_fastest = AsyncMock(return_value=[])
    service.get_approaches_in_period = AsyncMock(return_value=[])
    service.get_statistics = AsyncMock(return_value={})
    service.get_by_asteroid_id = AsyncMock(return_value=[])
    service.get_by_asteroid_designation = AsyncMock(return_value=[])
    return service


@pytest.fixture(scope="function")
def mock_threat_service():
    """Create a mock threat service with AsyncMock methods."""
    service = Mock()
    service.get_by_risk_level = AsyncMock(return_value=[])
    service.get_high_risk = AsyncMock(return_value=[])
    service.get_by_probability = AsyncMock(return_value=[])
    service.get_by_energy = AsyncMock(return_value=[])
    service.get_by_category = AsyncMock(return_value=[])
    service.get_statistics = AsyncMock(return_value={})
    service.get_by_designation = AsyncMock(return_value=None)
    return service


@pytest.fixture(scope="function")
def client(mock_asteroid_service, mock_approach_service, mock_threat_service):
    """Create a test client with mocked services.
    
    This fixture overrides the API dependencies with mock services
    for each test function, ensuring test isolation.
    """
    # Override dependencies
    app.dependency_overrides[get_asteroid_service] = lambda: mock_asteroid_service
    app.dependency_overrides[get_approach_service] = lambda: mock_approach_service
    app.dependency_overrides[get_threat_service] = lambda: mock_threat_service
    
    test_client = TestClient(app)
    yield test_client
    
    # Clean up overrides after test
    app.dependency_overrides.clear()
