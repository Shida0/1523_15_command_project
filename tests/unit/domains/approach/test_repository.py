import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from domains.approach.models.close_approach import CloseApproachModel
from domains.approach.repositories.approach_repository import ApproachRepository


class TestApproachRepository:
    """Unit tests for ApproachRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_asteroid(self, mock_session):
        """Test getting approaches by asteroid ID."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_by_asteroid(1)

        # Assert
        assert result == expected_approaches
        repo.filter.assert_called_once_with(
            filters={"asteroid_id": 1},
            skip=0,
            limit=100,
            order_by="approach_time"
        )

    @pytest.mark.asyncio
    async def test_get_by_asteroid_designation(self, mock_session):
        """Test getting approaches by asteroid designation."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_by_asteroid_designation("2023 DW")

        # Assert
        assert result == expected_approaches
        repo.filter.assert_called_once_with(
            filters={"asteroid_designation": "2023 DW"},
            skip=0,
            limit=100,
            order_by="approach_time"
        )

    @pytest.mark.asyncio
    async def test_get_approaches_in_period(self, mock_session):
        """Test getting approaches in a specific time period."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_approaches_in_period(
            start_date, end_date, max_distance=0.1
        )

        # Assert
        assert result == expected_approaches
        repo.filter.assert_called_once_with(
            filters={
                "approach_time__ge": start_date,
                "approach_time__le": end_date,
                "distance_au__le": 0.1
            },
            skip=0,
            limit=100,
            order_by="approach_time"
        )

    @pytest.mark.asyncio
    async def test_get_approaches_in_period_no_max_distance(self, mock_session):
        """Test getting approaches in a specific time period without max distance."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_approaches_in_period(
            start_date, end_date
        )

        # Assert
        assert result == expected_approaches
        repo.filter.assert_called_once_with(
            filters={
                "approach_time__ge": start_date,
                "approach_time__le": end_date
            },
            skip=0,
            limit=100,
            order_by="approach_time"
        )

    @pytest.mark.asyncio
    async def test_get_upcoming_approaches(self, mock_session):
        """Test getting upcoming approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(timezone.utc),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_upcoming_approaches(limit=10)

        # Assert
        assert result == expected_approaches
        # Check that the filter was called with the correct parameters
        repo.filter.assert_called_once()
        call_args = repo.filter.call_args
        assert call_args[1]['limit'] == 10
        assert call_args[1]['order_by'] == "approach_time"
        # Verify that the approach_time__ge filter includes the current time
        assert 'approach_time__ge' in call_args[1]['filters']

    @pytest.mark.asyncio
    async def test_get_closest_approaches_by_distance(self, mock_session):
        """Test getting closest approaches by distance."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_closest_approaches_by_distance(limit=10)

        # Assert
        assert result == expected_approaches
        repo.filter.assert_called_once_with(
            filters={},
            limit=10,
            order_by="distance_au"
        )

    @pytest.mark.asyncio
    async def test_get_fastest_approaches(self, mock_session):
        """Test getting fastest approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        expected_approaches = [
            CloseApproachModel(
                id=1,
                asteroid_id=1,
                approach_time=datetime.now(),
                distance_au=0.01,
                distance_km=1495978.707,
                velocity_km_s=10.5,
                asteroid_designation="2023 DW"
            )
        ]

        # Mock the filter method to return the approaches
        repo.filter = AsyncMock(return_value=expected_approaches)
        
        # Act
        result = await repo.get_fastest_approaches(limit=10)

        # Assert
        assert result == expected_approaches
        repo.filter.assert_called_once_with(
            filters={},
            limit=10,
            order_by="velocity_km_s",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_bulk_create_approaches(self, mock_session):
        """Test bulk creating approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        approaches_data = [
            {
                "asteroid_id": 1,
                "approach_time": datetime.now(),
                "distance_au": 0.01,
                "velocity_km_s": 10.5,
                "asteroid_designation": "2023 DW"
            }
        ]

        # Mock the bulk_create method
        repo.bulk_create = AsyncMock(return_value=(5, 2))  # 5 created, 2 updated

        # Act
        result = await repo.bulk_create_approaches(approaches_data, "batch_123")

        # Update the data with batch_id before checking
        expected_data = [item.copy() for item in approaches_data]
        for item in expected_data:
            item['calculation_batch_id'] = "batch_123"

        # Assert
        assert result == 7  # 5 + 2
        repo.bulk_create.assert_called_once_with(
            data_list=expected_data,
            conflict_action="update",
            conflict_fields=["asteroid_id", "approach_time"]
        )

    @pytest.mark.asyncio
    async def test_delete_old_approaches(self, mock_session):
        """Test deleting old approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session
        cutoff_date = datetime(2020, 1, 1)

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
    async def test_get_statistics_success(self, mock_session):
        """Test getting statistics for approaches."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Mock the SQLAlchemy queries
        mock_execute = AsyncMock()
        mock_result = Mock()
        mock_result.scalar = Mock()

        # Define scalar results for the specific queries in the right order
        # 1. future_query: select(func.count()).where(self.model.approach_time >= now)
        # 2. avg_distance_query: select(func.avg(self.model.distance_au))
        # 3. avg_velocity_query: select(func.avg(self.model.velocity_km_s))
        # 4. closest_query: select(func.min(self.model.distance_au))
        scalar_calls = []
        def mock_scalar_side_effect():
            if len(scalar_calls) == 0:  # future_count
                scalar_calls.append(1)
                return 50
            elif len(scalar_calls) == 1:  # avg_distance_au
                scalar_calls.append(1)
                return 20.5
            elif len(scalar_calls) == 2:  # avg_velocity
                scalar_calls.append(1)
                return 10.2
            elif len(scalar_calls) == 3:  # closest_au
                scalar_calls.append(1)
                return 0.01
            else:
                return 0  # Default value for any other calls

        mock_result.scalar.side_effect = mock_scalar_side_effect
        mock_execute.return_value = mock_result
        mock_session.execute = mock_execute

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
    async def test_get_statistics_empty_database(self, mock_session):
        """Test getting statistics when database is empty."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session

        # Mock the count method to return 0
        repo.count = AsyncMock(return_value=0)

        # Mock the SQLAlchemy queries to return None or 0
        mock_execute = AsyncMock()
        mock_scalar = Mock()

        # Set up scalar results for different queries (all 0 or None)
        scalar_results = [0, 0, None, None, None]
        scalar_iter = iter(scalar_results)
        mock_scalar.side_effect = lambda: next(scalar_iter) if next(iter([True]), None) else None

        def side_effect():
            val = next(scalar_iter)
            return val if val is not None else 0

        mock_scalar.side_effect = side_effect
        mock_execute.return_value.scalar = mock_scalar
        mock_session.execute = mock_execute

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_approaches"] == 0
        assert result["future_approaches"] == 0
        assert result["past_approaches"] == 0
        assert result["average_distance_au"] == 0
        assert result["average_velocity_km_s"] == 0
        assert result["closest_distance_au"] == 0
        assert result["closest_distance_km"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_exception_handling(self, mock_session):
        """Test that exceptions in get_statistics are properly handled."""
        # Arrange
        repo = ApproachRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Mock the SQLAlchemy queries to raise an exception
        mock_execute = AsyncMock()
        mock_execute.side_effect = Exception("Database error")
        mock_session.execute = mock_execute

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.get_statistics()