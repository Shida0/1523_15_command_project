"""
Unit tests for ApproachRepository.

These tests verify that repository methods correctly form SQL queries
by mocking session.execute() instead of internal methods.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from domains.approach.models.close_approach import CloseApproachModel
from domains.approach.repositories.approach_repository import ApproachRepository


class TestApproachRepository:
    """Unit tests for ApproachRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_asteroid(self, mock_session, sample_approach_data):
        """Test getting approaches by asteroid ID."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_asteroid(1, skip=0, limit=100)

        # Assert
        assert len(result) == 1
        assert result[0].asteroid_id == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_asteroid_with_pagination(self, mock_session, sample_approach_data):
        """Test getting approaches by asteroid ID with custom pagination."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_asteroid(1, skip=10, limit=50)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_asteroid_designation(self, mock_session, sample_approach_data):
        """Test getting approaches by asteroid designation."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_asteroid_designation("2023 TEST", skip=0, limit=100)

        # Assert
        assert len(result) == 1
        assert result[0].asteroid_designation == "2023 TEST"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_approaches_in_period(self, mock_session, sample_approach_data):
        """Test getting approaches in a specific time period."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        # Act
        result = await repo.get_approaches_in_period(
            start_date, end_date, max_distance=0.1, skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_approaches_in_period_no_max_distance(self, mock_session, sample_approach_data):
        """Test getting approaches in a specific time period without max distance."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        # Act
        result = await repo.get_approaches_in_period(
            start_date, end_date, skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_upcoming_approaches(self, mock_session, sample_approach_data):
        """Test getting upcoming approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_upcoming_approaches(limit=10)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_closest_approaches_by_distance(self, mock_session, sample_approach_data):
        """Test getting closest approaches by distance."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_closest_approaches_by_distance(limit=10)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_fastest_approaches(self, mock_session, sample_approach_data):
        """Test getting fastest approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        expected_approach = CloseApproachModel(**sample_approach_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_approach])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_fastest_approaches(limit=10)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_approaches(self, mock_session):
        """Test bulk creating approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        approaches_data = [
            {
                "asteroid_id": 1,
                "approach_time": datetime.now(timezone.utc),
                "distance_au": 0.01,
                "distance_km": 1495978.707,
                "velocity_km_s": 10.5,
                "asteroid_designation": "2023 DW",
                "data_source": "NASA CAD API"
            }
        ]

        # Mock the bulk_create method
        repo.bulk_create = AsyncMock(return_value=(5, 2))  # 5 created, 2 updated

        # Act
        result = await repo.bulk_create_approaches(approaches_data, "batch_123")

        # Assert
        assert result == 7  # 5 + 2
        repo.bulk_create.assert_called_once_with(
            data_list=approaches_data,
            conflict_action="update",
            conflict_fields=["asteroid_id", "approach_time"]
        )

    @pytest.mark.asyncio
    async def test_delete_old_approaches(self, mock_session):
        """Test deleting old approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        cutoff_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

        # Mock the bulk_delete method
        repo.bulk_delete = AsyncMock(return_value=5)

        # Act
        result = await repo.delete_old_approaches(cutoff_date)

        # Assert
        assert result == 5
        repo.bulk_delete.assert_called_once_with(
            filters={"approach_time__lt": cutoff_date}
        )

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, mock_session, ordered_scalar_mock):
        """Test getting statistics for approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Create ordered mock for scalar results
        # Order: future_count, avg_distance, avg_velocity, closest_distance
        mock_result = ordered_scalar_mock([50, 20.5, 10.2, 0.01])
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_approaches"] == 100
        assert result["future_approaches"] == 50
        assert result["past_approaches"] == 50  # 100 - 50
        assert result["average_distance_au"] == 20.5
        assert result["average_velocity_km_s"] == 10.2
        assert result["closest_distance_au"] == 0.01
        assert result["closest_distance_km"] == 0.01 * 149597870.7
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_get_statistics_empty_database(self, mock_session, ordered_scalar_mock):
        """Test getting statistics when database is empty."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session

        # Mock the count method to return 0
        repo.count = AsyncMock(return_value=0)

        # Create ordered mock for scalar results (all 0 or None)
        mock_result = ordered_scalar_mock([0, 0, None, None], default=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_approaches"] == 0
        assert result["future_approaches"] == 0
        assert result["past_approaches"] == 0
        assert result["average_distance_au"] == 0
        assert result["average_velocity_km_s"] == 0
        assert result["closest_distance_au"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_exception_handling(self, mock_session):
        """Test that exceptions in get_statistics are properly handled."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Mock the SQLAlchemy queries to raise an exception
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.get_statistics()

    @pytest.mark.asyncio
    async def test_count_method(self, mock_session):
        """Test count method returns correct value."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=42)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.count()

        # Assert
        assert result == 42
        mock_session.execute.assert_called_once()
