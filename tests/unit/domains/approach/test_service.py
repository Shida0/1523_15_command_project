import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from domains.approach.services.approach_service import ApproachService


class TestApproachService:
    """Unit tests for ApproachService class."""

    def test_approach_service_initialization(self):
        """Test initializing the approach service."""
        # Arrange
        mock_session_factory = Mock()
        
        # Act
        service = ApproachService(mock_session_factory)
        
        # Assert
        assert service.session_factory == mock_session_factory

    @pytest.mark.asyncio
    async def test_get_upcoming(self, mock_session_factory, sample_approach_data):
        """Test getting upcoming approaches."""
        # Arrange
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        
        expected_approach = Mock()
        expected_approach.__table__ = Mock()
        expected_approach.__table__.columns = []
        for key, value in sample_approach_data.items():
            setattr(expected_approach, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_approach.__table__.columns.append(mock_col)

        # Configure the repository method to return the expected result using AsyncMock
        mock_repo.get_upcoming_approaches = AsyncMock(return_value=[expected_approach])

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act
            result = await service.get_upcoming(limit=10)

            # Assert
            mock_repo.get_upcoming_approaches.assert_called_once_with(10)
            assert len(result) == 1
            assert result[0]["asteroid_id"] == sample_approach_data["asteroid_id"]

    @pytest.mark.asyncio
    async def test_get_closest(self, mock_session_factory, sample_approach_data):
        """Test getting closest approaches."""
        # Arrange
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        mock_session = Mock()
        mock_repo.session = mock_session

        # Extend sample_approach_data with distance_au which is expected by the model
        extended_approach_data = {**sample_approach_data, "distance_au": 0.67}
        
        # Create a simple object with the expected attributes instead of a complex mock
        from types import SimpleNamespace
        expected_approach = SimpleNamespace(**extended_approach_data)
        # Add the table structure for the _model_to_dict method
        expected_approach.__table__ = Mock()
        expected_approach.__table__.columns = []
        for key in extended_approach_data.keys():
            mock_col = Mock()
            mock_col.name = key
            expected_approach.__table__.columns.append(mock_col)

        # Configure the repository method to return the expected result as a coroutine
        mock_repo.get_closest_approaches_by_distance = AsyncMock(return_value=[expected_approach])

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act
            result = await service.get_closest(limit=10)

            # Assert
            mock_repo.get_closest_approaches_by_distance.assert_called_once_with(10)
            assert len(result) == 1
            assert result[0]["distance_au"] == 0.67  # Using the added value

    @pytest.mark.asyncio
    async def test_get_fastest(self, mock_session_factory, sample_approach_data):
        """Test getting fastest approaches."""
        # Arrange
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        mock_session = Mock()
        mock_repo.session = mock_session

        expected_approach = Mock()
        expected_approach.__table__ = Mock()
        expected_approach.__table__.columns = []
        for key, value in sample_approach_data.items():
            setattr(expected_approach, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_approach.__table__.columns.append(mock_col)

        # Configure the repository method to return the expected result as a coroutine
        mock_repo.get_fastest_approaches = AsyncMock(return_value=[expected_approach])

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act
            result = await service.get_fastest(limit=10)

            # Assert
            mock_repo.get_fastest_approaches.assert_called_once_with(10)
            assert len(result) == 1
            assert result[0]["velocity_km_s"] == sample_approach_data["velocity_km_s"]

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_session_factory):
        """Test getting approach statistics."""
        # Arrange
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        mock_session = Mock()
        mock_repo.session = mock_session

        expected_stats = {
            "total_approaches": 100,
            "future_approaches": 50,
            "past_approaches": 50,
            "average_distance_au": 0.05,
            "average_velocity_km_s": 10.5,
            "closest_distance_au": 0.01,
            "closest_distance_km": 1495978.707,
            "last_updated": "2023-01-01T00:00:00"
        }

        # Configure the repository method to return the expected result as a coroutine
        mock_repo.get_statistics = AsyncMock(return_value=expected_stats)

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act
            result = await service.get_statistics()

            # Assert
            mock_repo.get_statistics.assert_called_once()
            assert result == expected_stats

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id(self, mock_session_factory, sample_approach_data):
        """Test getting approaches by asteroid ID."""
        # Arrange
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        mock_session = Mock()
        mock_repo.session = mock_session

        expected_approach = Mock()
        expected_approach.__table__ = Mock()
        expected_approach.__table__.columns = []
        for key, value in sample_approach_data.items():
            setattr(expected_approach, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_approach.__table__.columns.append(mock_col)

        # Configure the repository method to return the expected result as a coroutine
        mock_repo.get_by_asteroid = AsyncMock(return_value=[expected_approach])

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act
            result = await service.get_by_asteroid_id(1)

            # Assert
            mock_repo.get_by_asteroid.assert_called_once_with(1)
            assert len(result) == 1
            assert result[0]["asteroid_id"] == sample_approach_data["asteroid_id"]

    @pytest.mark.asyncio
    async def test_get_by_asteroid_designation(self, mock_session_factory, sample_approach_data):
        """Test getting approaches by asteroid designation."""
        # Arrange
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        mock_session = Mock()
        mock_repo.session = mock_session

        # Extend sample_approach_data with distance_au which is expected by the model
        extended_approach_data = {**sample_approach_data, "distance_au": 0.67, "asteroid_designation": "2023 DW"}
        
        # Create a simple object with the expected attributes instead of a complex mock
        from types import SimpleNamespace
        expected_approach = SimpleNamespace(**extended_approach_data)
        # Add the table structure for the _model_to_dict method
        expected_approach.__table__ = Mock()
        expected_approach.__table__.columns = []
        for key in extended_approach_data.keys():
            mock_col = Mock()
            mock_col.name = key
            expected_approach.__table__.columns.append(mock_col)

        # Configure the repository method to return the expected result as a coroutine
        mock_repo.get_by_asteroid_designation = AsyncMock(return_value=[expected_approach])

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act
            result = await service.get_by_asteroid_designation("2023 DW")

            # Assert
            mock_repo.get_by_asteroid_designation.assert_called_once_with("2023 DW")
            assert len(result) == 1
            assert result[0]["asteroid_designation"] == "2023 DW"

    def test_model_to_dict_with_valid_model(self, sample_approach_data):
        """Test converting model instance to dictionary."""
        # Arrange
        service = ApproachService(Mock())
        
        mock_model = Mock()
        mock_model.__table__ = Mock()
        mock_model.__table__.columns = []
        
        for key, value in sample_approach_data.items():
            setattr(mock_model, key, value)
            mock_col = Mock()
            mock_col.name = key
            mock_model.__table__.columns.append(mock_col)
        
        # Act
        result = service._model_to_dict(mock_model)

        # Assert
        assert result is not None
        for key, expected_value in sample_approach_data.items():
            actual_value = result[key]
            # Handle type conversions that happen in _model_to_dict
            if hasattr(expected_value, 'isoformat'):  # datetime or date objects
                if hasattr(expected_value, 'hour'):  # datetime object (has hour attribute)
                    assert actual_value == expected_value.isoformat()
                else:  # date object (no hour attribute)
                    assert actual_value == expected_value.isoformat()
            elif hasattr(expected_value, 'quantize'):  # Decimal objects
                assert actual_value == float(expected_value)
            else:
                assert actual_value == expected_value

    def test_model_to_dict_with_none(self):
        """Test converting None model to dictionary."""
        # Arrange
        service = ApproachService(Mock())
        
        # Act
        result = service._model_to_dict(None)
        
        # Assert
        assert result is None

    def test_model_to_dict_with_relationships(self, sample_approach_data):
        """Test converting model instance with relationships to dictionary."""
        # Arrange
        service = ApproachService(Mock())

        # Use SimpleNamespace to avoid _mock_methods conflicts
        from types import SimpleNamespace
        
        mock_model = SimpleNamespace()
        mock_model.__dict__.update(sample_approach_data)
        
        # Create a mock table
        mock_table = Mock()
        mock_table.columns = []
        for key in sample_approach_data.keys():
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
        for key, expected_value in sample_approach_data.items():
            actual_value = result[key]
            # Handle type conversions that happen in _model_to_dict
            if hasattr(expected_value, 'isoformat'):  # datetime or date objects
                if hasattr(expected_value, 'hour'):  # datetime object (has hour attribute)
                    assert actual_value == expected_value.isoformat()
                else:  # date object (no hour attribute)
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
        service = ApproachService(mock_session_factory)

        # Create a fully mocked repository
        mock_repo = Mock()
        mock_session = Mock()
        mock_repo.session = mock_session

        # Configure the repository methods to return expected results as coroutines
        mock_repo.get_upcoming_approaches = AsyncMock(return_value=[])
        mock_repo.get_closest_approaches_by_distance = AsyncMock(return_value=[])
        mock_repo.get_fastest_approaches = AsyncMock(return_value=[])
        mock_repo.get_statistics = AsyncMock(return_value={})
        mock_repo.get_by_asteroid = AsyncMock(return_value=[])
        mock_repo.get_by_asteroid_designation = AsyncMock(return_value=[])

        # Mock the UoW with the mocked repository
        mock_uow = Mock()
        mock_uow.approach_repo = mock_repo

        # Since UnitOfWork is imported inside the function, we need to patch it at the module level
        # Patch the shared.transaction.uow module's UnitOfWork
        with patch('shared.transaction.uow.UnitOfWork') as MockUoWClass:
            mock_uow_instance = Mock()
            mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
            MockUoWClass.return_value = mock_uow_instance

            # Act - Call all the methods
            await service.get_upcoming(limit=10)
            await service.get_closest(limit=10)
            await service.get_fastest(limit=10)
            await service.get_statistics()
            await service.get_by_asteroid_id(1)
            await service.get_by_asteroid_designation("2023 DW")

            # Assert - All methods should have used UoW
            mock_repo.get_upcoming_approaches.assert_called_once_with(10)
            mock_repo.get_closest_approaches_by_distance.assert_called_once_with(10)
            mock_repo.get_fastest_approaches.assert_called_once_with(10)
            mock_repo.get_statistics.assert_called_once()
            mock_repo.get_by_asteroid.assert_called_once_with(1)
            mock_repo.get_by_asteroid_designation.assert_called_once_with("2023 DW")