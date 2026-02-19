"""
Unit tests for ApproachService.

These tests verify that service methods correctly pass pagination parameters
to repository methods.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, timedelta

from domains.approach.models.close_approach import CloseApproachModel
from domains.approach.services.approach_service import ApproachService


class TestApproachService:
    """Unit tests for ApproachService class."""

    def test_approach_service_initialization(self, mock_session_factory):
        """Test initializing the approach service."""
        # Arrange & Act
        service = ApproachService(mock_session_factory)

        # Assert
        assert service.session_factory == mock_session_factory

    @pytest.mark.asyncio
    async def test_get_upcoming(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting upcoming approaches."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_upcoming_approaches = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_upcoming(limit=10, skip=0)

            # Assert
            assert len(result) == 1
            assert result[0]["asteroid_id"] == sample_approach_data["asteroid_id"]
            mock_uow.approach_repo.get_upcoming_approaches.assert_called_once_with(limit=10, skip=0)

    @pytest.mark.asyncio
    async def test_get_upcoming_default_limit(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting upcoming approaches with default limit."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_upcoming_approaches = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_upcoming()

            # Assert
            assert len(result) == 1
            mock_uow.approach_repo.get_upcoming_approaches.assert_called_once_with(limit=10, skip=0)

    @pytest.mark.asyncio
    async def test_get_closest(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting closest approaches."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_closest_approaches_by_distance = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_closest(limit=10)

            # Assert
            assert len(result) == 1
            assert result[0]["distance_au"] == sample_approach_data["distance_au"]
            mock_uow.approach_repo.get_closest_approaches_by_distance.assert_called_once_with(limit=10, skip=0)

    @pytest.mark.asyncio
    async def test_get_fastest(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting fastest approaches."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_fastest_approaches = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_fastest(limit=10)

            # Assert
            assert len(result) == 1
            assert result[0]["velocity_km_s"] == sample_approach_data["velocity_km_s"]
            mock_uow.approach_repo.get_fastest_approaches.assert_called_once_with(limit=10, skip=0)

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_with_defaults(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting approaches by asteroid ID with default pagination."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_by_asteroid = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(1)

            # Assert
            assert len(result) == 1
            assert result[0]["asteroid_id"] == sample_approach_data["asteroid_id"]
            # Verify pagination parameters are passed with defaults
            mock_uow.approach_repo.get_by_asteroid.assert_called_once_with(
                1, skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_with_custom_pagination(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting approaches by asteroid ID with custom pagination."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_by_asteroid = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(1, skip=10, limit=50)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.approach_repo.get_by_asteroid.assert_called_once_with(
                1, skip=10, limit=50
            )

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_empty_result(self, mock_session_factory):
        """Test getting approaches by asteroid ID returns empty list when none found."""
        # Arrange
        service = ApproachService(mock_session_factory)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_by_asteroid = AsyncMock(return_value=[])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(999)

            # Assert
            assert result == []
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_by_asteroid_designation_with_defaults(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting approaches by asteroid designation with default pagination."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_by_asteroid_designation = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_designation("2023 TEST")

            # Assert
            assert len(result) == 1
            assert result[0]["asteroid_designation"] == "2023 TEST"
            # Verify pagination parameters are passed with defaults
            mock_uow.approach_repo.get_by_asteroid_designation.assert_called_once_with(
                "2023 TEST", skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_asteroid_designation_with_custom_pagination(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting approaches by asteroid designation with custom pagination."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_by_asteroid_designation = AsyncMock(
            return_value=[expected_approach]
        )

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_designation("2023 TEST", skip=5, limit=25)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.approach_repo.get_by_asteroid_designation.assert_called_once_with(
                "2023 TEST", skip=5, limit=25
            )

    @pytest.mark.asyncio
    async def test_get_approaches_in_period_with_defaults(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting approaches in period with default pagination."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_approaches_in_period = AsyncMock(
            return_value=[expected_approach]
        )
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_approaches_in_period(start_date, end_date)

            # Assert
            assert len(result) == 1
            # Verify pagination parameters are passed with defaults
            mock_uow.approach_repo.get_approaches_in_period.assert_called_once_with(
                start_date, end_date, max_distance=None, skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_approaches_in_period_with_max_distance(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test getting approaches in period with max_distance filter."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_approaches_in_period = AsyncMock(
            return_value=[expected_approach]
        )
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_approaches_in_period(
                start_date, end_date, max_distance=0.05, skip=10, limit=50
            )

            # Assert
            assert len(result) == 1
            # Verify all parameters are passed correctly
            mock_uow.approach_repo.get_approaches_in_period.assert_called_once_with(
                start_date, end_date, max_distance=0.05, skip=10, limit=50
            )

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_session_factory):
        """Test getting approach statistics."""
        # Arrange
        service = ApproachService(mock_session_factory)

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

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.approach_repo.get_statistics = AsyncMock(return_value=expected_stats)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_statistics()

            # Assert
            assert result == expected_stats
            mock_uow.approach_repo.get_statistics.assert_called_once()

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
            if hasattr(expected_value, 'isoformat'):
                assert actual_value == expected_value.isoformat()
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

    @pytest.mark.asyncio
    async def test_all_methods_use_uow_correctly(self, mock_session_factory, sample_approach_data, create_mock_model):
        """Test that all service methods properly use UnitOfWork."""
        # Arrange
        service = ApproachService(mock_session_factory)
        expected_approach = create_mock_model(CloseApproachModel, sample_approach_data)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_uow.approach_repo.get_upcoming_approaches = AsyncMock(return_value=[expected_approach])
        mock_uow.approach_repo.get_closest_approaches_by_distance = AsyncMock(return_value=[expected_approach])
        mock_uow.approach_repo.get_fastest_approaches = AsyncMock(return_value=[expected_approach])
        mock_uow.approach_repo.get_statistics = AsyncMock(return_value={})
        mock_uow.approach_repo.get_by_asteroid = AsyncMock(return_value=[expected_approach])
        mock_uow.approach_repo.get_by_asteroid_designation = AsyncMock(return_value=[expected_approach])
        mock_uow.approach_repo.get_approaches_in_period = AsyncMock(return_value=[expected_approach])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act - Call all methods
            start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
            
            await service.get_upcoming(limit=10)
            await service.get_closest(limit=10)
            await service.get_fastest(limit=10)
            await service.get_statistics()
            await service.get_by_asteroid_id(1, skip=0, limit=100)
            await service.get_by_asteroid_designation("2023 TEST", skip=0, limit=100)
            await service.get_approaches_in_period(start_date, end_date)

            # Assert - All methods should have used UoW
            mock_uow.approach_repo.get_upcoming_approaches.assert_called_once_with(limit=10, skip=0)
            mock_uow.approach_repo.get_closest_approaches_by_distance.assert_called_once_with(limit=10, skip=0)
            mock_uow.approach_repo.get_fastest_approaches.assert_called_once_with(limit=10, skip=0)
            mock_uow.approach_repo.get_statistics.assert_called_once()
            mock_uow.approach_repo.get_by_asteroid.assert_called_once_with(1, skip=0, limit=100)
            mock_uow.approach_repo.get_by_asteroid_designation.assert_called_once_with(
                "2023 TEST", skip=0, limit=100
            )
            mock_uow.approach_repo.get_approaches_in_period.assert_called_once_with(
                start_date, end_date, max_distance=None, skip=0, limit=100
            )
