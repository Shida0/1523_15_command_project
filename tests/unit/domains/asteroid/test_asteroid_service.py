"""
Unit tests for AsteroidService.

These tests verify that service methods correctly pass pagination parameters
to repository methods.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from domains.asteroid.models.asteroid import AsteroidModel
from domains.asteroid.services.asteroid_service import AsteroidService


class TestAsteroidService:
    """Unit tests for AsteroidService class."""

    def test_asteroid_service_initialization(self, mock_session_factory):
        """Test initializing the asteroid service."""
        # Act
        service = AsteroidService(mock_session_factory)

        # Assert
        assert service.session_factory == mock_session_factory

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting an asteroid by designation when found."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        
        expected_asteroid = create_mock_model(AsteroidModel, sample_asteroid_data)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_by_designation = AsyncMock(return_value=expected_asteroid)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("2023 TEST")

            # Assert
            assert result is not None
            assert result["designation"] == "2023 TEST"
            mock_uow.asteroid_repo.get_by_designation.assert_called_once_with("2023 TEST")

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session_factory):
        """Test getting an asteroid by designation when not found."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_by_designation = AsyncMock(return_value=None)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("nonexistent")

            # Assert
            assert result is None
            mock_uow.asteroid_repo.get_by_designation.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_by_moid_with_defaults(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting asteroids by MOID with default pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        expected_asteroid = create_mock_model(AsteroidModel, sample_asteroid_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_by_earth_moid = AsyncMock(
            return_value=[expected_asteroid]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_moid(0.05)

            # Assert
            assert len(result) == 1
            # Verify pagination parameters are passed with defaults
            mock_uow.asteroid_repo.get_asteroids_by_earth_moid.assert_called_once_with(
                0.05, skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_moid_with_custom_pagination(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting asteroids by MOID with custom pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        expected_asteroid = create_mock_model(AsteroidModel, sample_asteroid_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_by_earth_moid = AsyncMock(
            return_value=[expected_asteroid]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_moid(0.05, skip=10, limit=50)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.asteroid_repo.get_asteroids_by_earth_moid.assert_called_once_with(
                0.05, skip=10, limit=50
            )

    @pytest.mark.asyncio
    async def test_get_by_moid_empty_result(self, mock_session_factory):
        """Test getting asteroids by MOID returns empty list when none found."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_by_earth_moid = AsyncMock(return_value=[])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_moid(0.05)

            # Assert
            assert result == []
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_by_orbit_class_with_defaults(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting asteroids by orbit class with default pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        data = {**sample_asteroid_data, "orbit_class": "Apollo"}
        expected_asteroid = create_mock_model(AsteroidModel, data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_by_orbit_class = AsyncMock(
            return_value=[expected_asteroid]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_orbit_class("Apollo")

            # Assert
            assert len(result) == 1
            assert result[0]["orbit_class"] == "Apollo"
            # Verify pagination parameters are passed with defaults
            mock_uow.asteroid_repo.get_asteroids_by_orbit_class.assert_called_once_with(
                "Apollo", skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_orbit_class_with_custom_pagination(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting asteroids by orbit class with custom pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        data = {**sample_asteroid_data, "orbit_class": "Aten"}
        expected_asteroid = create_mock_model(AsteroidModel, data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_by_orbit_class = AsyncMock(
            return_value=[expected_asteroid]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_orbit_class("Aten", skip=20, limit=30)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.asteroid_repo.get_asteroids_by_orbit_class.assert_called_once_with(
                "Aten", skip=20, limit=30
            )

    @pytest.mark.asyncio
    async def test_get_with_accurate_diameter_with_defaults(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting asteroids with accurate diameter with default pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        data = {**sample_asteroid_data, "accurate_diameter": True}
        expected_asteroid = create_mock_model(AsteroidModel, data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter = AsyncMock(
            return_value=[expected_asteroid]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_with_accurate_diameter()

            # Assert
            assert len(result) == 1
            assert result[0]["accurate_diameter"] is True
            # Verify pagination parameters are passed with defaults
            mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter.assert_called_once_with(
                skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_with_accurate_diameter_with_custom_pagination(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test getting asteroids with accurate diameter with custom pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        data = {**sample_asteroid_data, "accurate_diameter": True}
        expected_asteroid = create_mock_model(AsteroidModel, data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter = AsyncMock(
            return_value=[expected_asteroid]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_with_accurate_diameter(skip=5, limit=25)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter.assert_called_once_with(
                skip=5, limit=25
            )

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_session_factory):
        """Test getting asteroid statistics."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        expected_stats = {
            "total_asteroids": 100,
            "average_diameter_km": 0.15,
            "min_earth_moid_au": 0.01,
            "accurate_diameter_count": 10,
            "percent_accurate": 10.0,
            "diameter_source_stats": {"measured": 20, "computed": 30, "calculated": 50},
            "last_updated": "2023-01-01T00:00:00"
        }

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_statistics = AsyncMock(return_value=expected_stats)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_statistics()

            # Assert
            assert result == expected_stats
            mock_uow.asteroid_repo.get_statistics.assert_called_once()

    def test_model_to_dict_with_valid_model(self, sample_asteroid_data):
        """Test converting model instance to dictionary."""
        # Arrange
        service = AsteroidService(Mock())

        mock_model = Mock()
        mock_model.__table__ = Mock()
        mock_model.__table__.columns = []

        for key, value in sample_asteroid_data.items():
            setattr(mock_model, key, value)
            mock_col = Mock()
            mock_col.name = key
            mock_model.__table__.columns.append(mock_col)

        # Act
        result = service._model_to_dict(mock_model)

        # Assert
        assert result is not None
        for key, expected_value in sample_asteroid_data.items():
            actual_value = result[key]
            # Handle type conversions that happen in _model_to_dict
            if hasattr(expected_value, 'isoformat'):  # datetime objects
                assert actual_value == expected_value.isoformat()
            else:
                assert actual_value == expected_value

    def test_model_to_dict_with_none(self):
        """Test converting None model to dictionary."""
        # Arrange
        service = AsteroidService(Mock())

        # Act
        result = service._model_to_dict(None)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_all_methods_use_uow_correctly(self, mock_session_factory, sample_asteroid_data, create_mock_model):
        """Test that all service methods properly use UnitOfWork with pagination."""
        # Arrange
        service = AsteroidService(mock_session_factory)
        expected_asteroid = create_mock_model(AsteroidModel, sample_asteroid_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_uow.asteroid_repo.get_by_designation = AsyncMock(return_value=expected_asteroid)
        mock_uow.asteroid_repo.get_asteroids_by_earth_moid = AsyncMock(return_value=[expected_asteroid])
        mock_uow.asteroid_repo.get_asteroids_by_orbit_class = AsyncMock(return_value=[expected_asteroid])
        mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter = AsyncMock(return_value=[expected_asteroid])
        mock_uow.asteroid_repo.get_statistics = AsyncMock(return_value={})

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act - Call all methods
            await service.get_by_designation("2023 TEST")
            await service.get_by_moid(0.05, skip=0, limit=100)
            await service.get_by_orbit_class("Apollo", skip=0, limit=100)
            await service.get_with_accurate_diameter(skip=0, limit=100)
            await service.get_statistics()

            # Assert - All methods should have used UoW with correct pagination
            mock_uow.asteroid_repo.get_by_designation.assert_called_once_with("2023 TEST")
            mock_uow.asteroid_repo.get_asteroids_by_earth_moid.assert_called_once_with(
                0.05, skip=0, limit=100
            )
            mock_uow.asteroid_repo.get_asteroids_by_orbit_class.assert_called_once_with(
                "Apollo", skip=0, limit=100
            )
            mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter.assert_called_once_with(
                skip=0, limit=100
            )
            mock_uow.asteroid_repo.get_statistics.assert_called_once()
