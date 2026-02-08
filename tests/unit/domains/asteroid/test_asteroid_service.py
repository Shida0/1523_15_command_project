import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from domains.asteroid.services.asteroid_service import AsteroidService


class TestAsteroidService:
    """Unit tests for AsteroidService class."""

    def test_asteroid_service_initialization(self):
        """Test initializing the asteroid service."""
        # Arrange
        mock_session_factory = Mock()
        
        # Act
        service = AsteroidService(mock_session_factory)
        
        # Assert
        assert service.session_factory == mock_session_factory

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session_factory, sample_asteroid_data):
        """Test getting an asteroid by designation when found."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session

        expected_asteroid = Mock()
        expected_asteroid.__table__ = Mock()
        expected_asteroid.__table__.columns = []
        for key, value in sample_asteroid_data.items():
            # For the designation field, use the value passed to the method
            actual_value = "2023 DW" if key == "designation" else value
            setattr(expected_asteroid, key, actual_value)
            # Also add the attribute to the mock's __dict__ to make it accessible
            expected_asteroid.__dict__[key] = actual_value
            mock_col = Mock()
            mock_col.name = key
            expected_asteroid.__table__.columns.append(mock_col)

        mock_uow.asteroid_repo.get_by_designation = AsyncMock(return_value=expected_asteroid)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("2023 DW")

            # Assert
            assert result is not None
            assert result["designation"] == "2023 DW"
            assert result["name"] == sample_asteroid_data["name"]
            mock_uow.asteroid_repo.get_by_designation.assert_called_once_with("2023 DW")

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session_factory):
        """Test getting an asteroid by designation when not found."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session
        mock_uow.asteroid_repo.get_by_designation = AsyncMock(return_value=None)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("nonexistent")

            # Assert
            assert result is None
            mock_uow.asteroid_repo.get_by_designation.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_by_moid(self, mock_session_factory, sample_asteroid_data):
        """Test getting asteroids by MOID."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session

        expected_asteroid = Mock()
        expected_asteroid.__table__ = Mock()
        expected_asteroid.__table__.columns = []
        for key, value in sample_asteroid_data.items():
            setattr(expected_asteroid, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_asteroid.__table__.columns.append(mock_col)

        mock_uow.asteroid_repo.get_asteroids_by_earth_moid = AsyncMock(return_value=[expected_asteroid])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_moid(0.05)

            # Assert
            assert len(result) == 1
            assert result[0]["designation"] == sample_asteroid_data["designation"]
            mock_uow.asteroid_repo.get_asteroids_by_earth_moid.assert_called_once_with(0.05)

    @pytest.mark.asyncio
    async def test_get_by_orbit_class(self, mock_session_factory, sample_asteroid_data):
        """Test getting asteroids by orbit class."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session

        # Extend sample_asteroid_data with orbit_class which is expected by the test
        extended_asteroid_data = {**sample_asteroid_data, "orbit_class": "Apollo"}
        
        # Create a simple object with the expected attributes instead of a complex mock
        from types import SimpleNamespace
        expected_asteroid = SimpleNamespace(**extended_asteroid_data)
        # Add the table structure for the _model_to_dict method
        expected_asteroid.__table__ = Mock()
        expected_asteroid.__table__.columns = []
        for key in extended_asteroid_data.keys():
            mock_col = Mock()
            mock_col.name = key
            expected_asteroid.__table__.columns.append(mock_col)

        mock_uow.asteroid_repo.get_asteroids_by_orbit_class = AsyncMock(return_value=[expected_asteroid])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_orbit_class("Apollo")

            # Assert
            assert len(result) == 1
            assert result[0]["orbit_class"] == "Apollo"
            mock_uow.asteroid_repo.get_asteroids_by_orbit_class.assert_called_once_with("Apollo")

    @pytest.mark.asyncio
    async def test_get_with_accurate_diameter(self, mock_session_factory, sample_asteroid_data):
        """Test getting asteroids with accurate diameter."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session

        # Extend sample_asteroid_data with accurate_diameter which is expected by the test
        extended_asteroid_data = {**sample_asteroid_data, "accurate_diameter": True}
        
        # Create a simple object with the expected attributes instead of a complex mock
        from types import SimpleNamespace
        expected_asteroid = SimpleNamespace(**extended_asteroid_data)
        # Add the table structure for the _model_to_dict method
        expected_asteroid.__table__ = Mock()
        expected_asteroid.__table__.columns = []
        for key in extended_asteroid_data.keys():
            mock_col = Mock()
            mock_col.name = key
            expected_asteroid.__table__.columns.append(mock_col)

        mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter = AsyncMock(return_value=[expected_asteroid])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_with_accurate_diameter()

            # Assert
            assert len(result) == 1
            assert result[0]["accurate_diameter"] is True
            mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_session_factory):
        """Test getting asteroid statistics."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session

        expected_stats = {
            "total_asteroids": 100,
            "average_diameter_km": 0.1,
            "min_earth_moid_au": 0.05,
            "accurate_diameter_count": 10,
            "percent_accurate": 10.0,
            "diameter_source_stats": {"measured": 20, "computed": 30, "calculated": 50},
            "last_updated": "2023-01-01T00:00:00"
        }

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
            elif hasattr(expected_value, 'quantize'):  # Decimal objects
                assert actual_value == float(expected_value)
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

    def test_model_to_dict_with_relationships(self, sample_asteroid_data):
        """Test converting model instance with relationships to dictionary."""
        # Arrange
        service = AsteroidService(Mock())

        # Use SimpleNamespace to avoid _mock_methods conflicts
        from types import SimpleNamespace

        mock_model = SimpleNamespace()
        mock_model.__dict__.update(sample_asteroid_data)

        # Create a mock table
        mock_table = Mock()
        mock_table.columns = []
        for key in sample_asteroid_data.keys():
            mock_col = Mock()
            mock_col.name = key
            mock_table.columns.append(mock_col)
        mock_model.__table__ = mock_table

        # Add a relationship attribute
        mock_related_model = SimpleNamespace(id=1, name="Related")
        mock_related_table = Mock()
        mock_related_table.columns = []
        for attr in ["id", "name"]:
            mock_col = Mock()
            mock_col.name = attr
            mock_related_table.columns.append(mock_col)
        mock_related_model.__table__ = mock_related_table

        mock_model.related_field = mock_related_model

        # Act
        result = service._model_to_dict(mock_model)

        # Assert
        assert result is not None
        for key, expected_value in sample_asteroid_data.items():
            actual_value = result[key]
            # Handle type conversions that happen in _model_to_dict
            if hasattr(expected_value, 'isoformat'):  # datetime objects
                assert actual_value == expected_value.isoformat()
            elif hasattr(expected_value, 'quantize'):  # Decimal objects
                assert actual_value == float(expected_value)
            else:
                assert actual_value == expected_value
        assert "related_field" in result

    @pytest.mark.asyncio
    async def test_service_methods_use_uow_properly(self, mock_session_factory):
        """Test that all service methods properly use UnitOfWork."""
        # Arrange
        service = AsteroidService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.asteroid_repo = Mock()
        mock_session = Mock()
        mock_uow.asteroid_repo.session = mock_session
        
        mock_uow.asteroid_repo.get_by_designation = AsyncMock(return_value=None)
        mock_uow.asteroid_repo.get_asteroids_by_earth_moid = AsyncMock(return_value=[])
        mock_uow.asteroid_repo.get_asteroids_by_orbit_class = AsyncMock(return_value=[])
        mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter = AsyncMock(return_value=[])
        mock_uow.asteroid_repo.get_statistics = AsyncMock(return_value={})

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act - Call all the methods
            await service.get_by_designation("2023 DW")
            await service.get_by_moid(0.05)
            await service.get_by_orbit_class("Apollo")
            await service.get_with_accurate_diameter()
            await service.get_statistics()

            # Assert - All methods should have used UoW
            mock_uow.asteroid_repo.get_by_designation.assert_called_once_with("2023 DW")
            mock_uow.asteroid_repo.get_asteroids_by_earth_moid.assert_called_once_with(0.05)
            mock_uow.asteroid_repo.get_asteroids_by_orbit_class.assert_called_once_with("Apollo")
            mock_uow.asteroid_repo.get_asteroids_with_accurate_diameter.assert_called_once_with()
            mock_uow.asteroid_repo.get_statistics.assert_called_once()