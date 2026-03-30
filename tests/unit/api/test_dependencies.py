import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from api.dependencies import (
    get_uow,
    get_asteroid_service,
    get_approach_service,
    get_threat_service,
    async_session_factory
)
from shared.transaction.uow import UnitOfWork
from domains.asteroid.services.asteroid_service import AsteroidService
from domains.approach.services.approach_service import ApproachService
from domains.threat.services.threat_service import ThreatService


class TestAPIDependencies:
    """Unit tests for API dependencies."""

    def test_async_session_factory_defined(self):
        """Test that async_session_factory is defined."""
        # Assert
        assert async_session_factory is not None

    @pytest.mark.asyncio
    async def test_get_uow(self):
        """Test getting UnitOfWork dependency."""
        # Act
        uow = await get_uow()

        # Assert
        assert isinstance(uow, UnitOfWork)
        assert uow.session_factory == async_session_factory

    @pytest.mark.asyncio
    async def test_get_asteroid_service(self):
        """Test getting AsteroidService dependency."""
        # Act
        service = get_asteroid_service()

        # Assert
        assert isinstance(service, AsteroidService)
        assert service.session_factory == async_session_factory

    @pytest.mark.asyncio
    async def test_get_approach_service(self):
        """Test getting ApproachService dependency."""
        # Act
        service = get_approach_service()

        # Assert
        assert isinstance(service, ApproachService)
        assert service.session_factory == async_session_factory

    @pytest.mark.asyncio
    async def test_get_threat_service(self):
        """Test getting ThreatService dependency."""
        # Act
        service = get_threat_service()

        # Assert
        assert isinstance(service, ThreatService)
        assert service.session_factory == async_session_factory

    @pytest.mark.asyncio
    async def test_uow_dependency_consistency(self):
        """Test that UOW dependency creates consistent instances."""
        # Act
        uow1 = await get_uow()
        uow2 = await get_uow()

        # Assert
        assert isinstance(uow1, UnitOfWork)
        assert isinstance(uow2, UnitOfWork)
        # Both should use the same session factory
        assert uow1.session_factory == uow2.session_factory
        assert uow1.session_factory == async_session_factory

    @pytest.mark.asyncio
    async def test_service_factories_consistency(self):
        """Test that service factories create consistent instances."""
        # Act
        asteroid_service1 = get_asteroid_service()
        asteroid_service2 = get_asteroid_service()
        approach_service1 = get_approach_service()
        threat_service1 = get_threat_service()

        # Assert
        # All asteroid services should use the same session factory
        assert asteroid_service1.session_factory == asteroid_service2.session_factory
        assert asteroid_service1.session_factory == async_session_factory

        # All services should use the same session factory
        assert approach_service1.session_factory == async_session_factory
        assert threat_service1.session_factory == async_session_factory

    @pytest.mark.asyncio
    async def test_dependency_injection_with_mock_session_factory(self):
        """Test dependency injection with mocked session factory."""
        # Arrange
        mock_session_factory = Mock()

        # Temporarily replace the session factory for testing
        original_factory = async_session_factory

        # Since we can't directly modify the module variable in a test,
        # we'll test the constructors directly with a mock
        with patch('api.dependencies.async_session_factory', mock_session_factory):
            # Act
            uow = await get_uow()
            asteroid_service = get_asteroid_service()
            approach_service = get_approach_service()
            threat_service = get_threat_service()

            # Assert
            assert uow.session_factory == mock_session_factory
            assert asteroid_service.session_factory == mock_session_factory
            assert approach_service.session_factory == mock_session_factory
            assert threat_service.session_factory == mock_session_factory

    def test_dependency_modules_import_correctly(self):
        """Test that all required modules can be imported correctly."""
        # This test ensures that the imports in dependencies.py work
        # The fact that we reached this point means the imports worked
        
        # Test that the expected classes exist
        assert hasattr(UnitOfWork, '__init__')
        assert hasattr(AsteroidService, '__init__')
        assert hasattr(ApproachService, '__init__')
        assert hasattr(ThreatService, '__init__')

    @pytest.mark.asyncio
    async def test_uow_dependency_has_expected_interface(self):
        """Test that UOW dependency has the expected interface."""
        # Act
        uow = await get_uow()

        # Assert
        # Check that UOW has the expected repository attributes
        assert hasattr(uow, 'asteroid_repo')
        assert hasattr(uow, 'approach_repo')
        assert hasattr(uow, 'threat_repo')
        # These should be None until the UOW context is entered
        assert uow.asteroid_repo is None
        assert uow.approach_repo is None
        assert uow.threat_repo is None

    @pytest.mark.asyncio
    async def test_service_dependencies_have_expected_interface(self):
        """Test that service dependencies have the expected interface."""
        # Act
        asteroid_service = get_asteroid_service()
        approach_service = get_approach_service()
        threat_service = get_threat_service()

        # Assert
        # Check that services have expected methods
        assert hasattr(asteroid_service, 'get_by_designation')
        assert hasattr(approach_service, 'get_upcoming')
        assert hasattr(threat_service, 'get_by_designation')

        # Check that they all have the session_factory attribute
        assert hasattr(asteroid_service, 'session_factory')
        assert hasattr(approach_service, 'session_factory')
        assert hasattr(threat_service, 'session_factory')