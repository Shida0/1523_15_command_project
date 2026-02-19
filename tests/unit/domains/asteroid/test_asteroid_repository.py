"""
Unit tests for AsteroidRepository.

These tests verify that repository methods correctly form SQL queries
by mocking session.execute() instead of internal methods.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from domains.asteroid.models.asteroid import AsteroidModel
from domains.asteroid.repositories.asteroid_repository import AsteroidRepository


class TestAsteroidRepository:
    """Unit tests for AsteroidRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session, sample_asteroid_data):
        """Test getting an asteroid by designation when found."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        # Mock the result of session.execute
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=expected_asteroid)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_designation("2023 TEST")

        # Assert
        assert result == expected_asteroid
        mock_session.execute.assert_called_once()
        
        # Verify the query structure
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        # Check that query has the expected structure (is a Select object)
        assert hasattr(query, '_where_criteria')

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session):
        """Test getting an asteroid by designation when not found."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        # Mock the result to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_designation("nonexistent")

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_by_name_or_designation(self, mock_session, sample_asteroid_data):
        """Test searching asteroids by name or designation."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        # Mock scalars result
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.search_by_name_or_designation("Test", skip=10, limit=20)

        # Assert
        assert len(result) == 1
        assert result[0].designation == "2023 TEST"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_asteroids_by_diameter_range(self, mock_session, sample_asteroid_data):
        """Test getting asteroids by diameter range."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_asteroids_by_diameter_range(
            min_diameter=0.05, max_diameter=0.2, skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_asteroids_by_diameter_range_min_only(self, mock_session, sample_asteroid_data):
        """Test getting asteroids by minimum diameter only."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_asteroids_by_diameter_range(min_diameter=0.05)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_asteroids_by_diameter_range_max_only(self, mock_session, sample_asteroid_data):
        """Test getting asteroids by maximum diameter only."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_asteroids_by_diameter_range(max_diameter=0.2)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_asteroids_by_earth_moid(self, mock_session, sample_asteroid_data):
        """Test getting asteroids by Earth MOID."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_asteroids_by_earth_moid(0.1, skip=5, limit=50)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_asteroids_with_accurate_diameter(self, mock_session, sample_asteroid_data):
        """Test getting asteroids with accurate diameter."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        # Create asteroid with accurate_diameter=True
        data = {**sample_asteroid_data, "accurate_diameter": True}
        expected_asteroid = AsteroidModel(**data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_asteroids_with_accurate_diameter(skip=0, limit=100)

        # Assert
        assert len(result) == 1
        assert result[0].accurate_diameter is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_asteroids_by_orbit_class(self, mock_session, sample_asteroid_data):
        """Test getting asteroids by orbit class."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        data = {**sample_asteroid_data, "orbit_class": "Apollo"}
        expected_asteroid = AsteroidModel(**data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_asteroids_by_orbit_class("Apollo", skip=0, limit=100)

        # Assert
        assert len(result) == 1
        assert result[0].orbit_class == "Apollo"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, mock_session, ordered_scalar_mock):
        """Test getting statistics for asteroids."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Create ordered mock for scalar results
        # Order: avg_diameter, min_moid, accurate_count, measured, computed, calculated
        mock_result = ordered_scalar_mock([50.0, 0.01, 10, 20, 30, 50])
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_asteroids"] == 100
        assert result["average_diameter_km"] == 50.0
        assert result["min_earth_moid_au"] == 0.01
        assert result["accurate_diameter_count"] == 10
        assert result["percent_accurate"] == 10.0
        assert result["diameter_source_stats"] == {
            "measured": 20,
            "computed": 30,
            "calculated": 50
        }
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_get_statistics_empty_database(self, mock_session, ordered_scalar_mock):
        """Test getting statistics when database is empty."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session

        # Mock the count method to return 0
        repo.count = AsyncMock(return_value=0)

        # Create ordered mock for scalar results (all None or 0)
        mock_result = ordered_scalar_mock([None, None, 0, 0, 0, 0], default=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_asteroids"] == 0
        assert result["average_diameter_km"] == 0
        assert result["min_earth_moid_au"] == 0
        assert result["accurate_diameter_count"] == 0
        assert result["percent_accurate"] == 0

    @pytest.mark.asyncio
    async def test_bulk_create_asteroids(self, mock_session):
        """Test bulk creating asteroids."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        asteroids_data = [
            {
                "designation": "2023 DW",
                "name": "Test Asteroid",
                "absolute_magnitude": 20.5,
                "estimated_diameter_km": 0.1,
                "albedo": 0.15,
                "accurate_diameter": False,
                "diameter_source": "calculated"
            }
        ]

        # Mock the bulk_create method
        repo.bulk_create = AsyncMock(return_value=(1, 0))

        # Act
        created, updated = await repo.bulk_create_asteroids(asteroids_data)

        # Assert
        assert created == 1
        assert updated == 0
        repo.bulk_create.assert_called_once_with(
            data_list=asteroids_data,
            conflict_action="update",
            conflict_fields=["designation"]
        )

    @pytest.mark.asyncio
    async def test_get_statistics_exception_handling(self, mock_session):
        """Test that exceptions in get_statistics are properly handled."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Mock the SQLAlchemy queries to raise an exception
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.get_statistics()

    @pytest.mark.asyncio
    async def test_filter_method_with_pagination(self, mock_session, sample_asteroid_data):
        """Test that filter method correctly applies skip and limit."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        expected_asteroid = AsteroidModel(**sample_asteroid_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_asteroid])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.filter(
            filters={"orbit_class": "Apollo"},
            skip=10,
            limit=20,
            order_by="designation"
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_method(self, mock_session):
        """Test count method returns correct value."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=42)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.count()

        # Assert
        assert result == 42
        mock_session.execute.assert_called_once()
