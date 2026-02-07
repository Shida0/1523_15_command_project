import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domains.asteroid.models.asteroid import AsteroidModel
from domains.asteroid.repositories.asteroid_repository import AsteroidRepository


class TestAsteroidRepository:
    """Unit tests for AsteroidRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session):
        """Test getting an asteroid by designation when found."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0.15
        )

        # Mock the _find_by_fields method to return the asteroid
        repo._find_by_fields = AsyncMock(return_value=expected_asteroid)
        
        # Act
        result = await repo.get_by_designation("2023 DW")

        # Assert
        assert result == expected_asteroid
        repo._find_by_fields.assert_called_once_with({"designation": "2023 DW"})

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session):
        """Test getting an asteroid by designation when not found."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session

        # Mock the _find_by_fields method to return None
        repo._find_by_fields = AsyncMock(return_value=None)
        
        # Act
        result = await repo.get_by_designation("nonexistent")

        # Assert
        assert result is None
        repo._find_by_fields.assert_called_once_with({"designation": "nonexistent"})

    @pytest.mark.asyncio
    async def test_search_by_name_or_designation(self, mock_session):
        """Test searching asteroids by name or designation."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                name="Test Asteroid",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15
            )
        ]

        # Mock the search method to return the asteroids
        repo.search = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.search_by_name_or_designation("Test")

        # Assert
        assert result == expected_asteroids
        repo.search.assert_called_once_with(
            search_term="Test",
            search_fields=["name", "designation"],
            skip=0,
            limit=50
        )

    @pytest.mark.asyncio
    async def test_get_asteroids_by_diameter_range(self, mock_session):
        """Test getting asteroids by diameter range."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15
            )
        ]

        # Mock the filter method to return the asteroids
        repo.filter = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.get_asteroids_by_diameter_range(
            min_diameter=0.05, max_diameter=0.2
        )

        # Assert
        assert result == expected_asteroids
        repo.filter.assert_called_once_with(
            filters={
                "estimated_diameter_km__ge": 0.05,
                "estimated_diameter_km__le": 0.2
            },
            skip=0,
            limit=100,
            order_by="estimated_diameter_km"
        )

    @pytest.mark.asyncio
    async def test_get_asteroids_by_diameter_range_min_only(self, mock_session):
        """Test getting asteroids by minimum diameter only."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15
            )
        ]

        # Mock the filter method to return the asteroids
        repo.filter = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.get_asteroids_by_diameter_range(
            min_diameter=0.05
        )

        # Assert
        assert result == expected_asteroids
        repo.filter.assert_called_once_with(
            filters={"estimated_diameter_km__ge": 0.05},
            skip=0,
            limit=100,
            order_by="estimated_diameter_km"
        )

    @pytest.mark.asyncio
    async def test_get_asteroids_by_diameter_range_max_only(self, mock_session):
        """Test getting asteroids by maximum diameter only."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15
            )
        ]

        # Mock the filter method to return the asteroids
        repo.filter = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.get_asteroids_by_diameter_range(
            max_diameter=0.2
        )

        # Assert
        assert result == expected_asteroids
        repo.filter.assert_called_once_with(
            filters={"estimated_diameter_km__le": 0.2},
            skip=0,
            limit=100,
            order_by="estimated_diameter_km"
        )

    @pytest.mark.asyncio
    async def test_get_asteroids_by_earth_moid(self, mock_session):
        """Test getting asteroids by Earth MOID."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15,
                earth_moid_au=0.05
            )
        ]

        # Mock the filter method to return the asteroids
        repo.filter = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.get_asteroids_by_earth_moid(0.1)

        # Assert
        assert result == expected_asteroids
        repo.filter.assert_called_once_with(
            filters={"earth_moid_au__le": 0.1},
            skip=0,
            limit=100,
            order_by="earth_moid_au"
        )

    @pytest.mark.asyncio
    async def test_get_asteroids_with_accurate_diameter(self, mock_session):
        """Test getting asteroids with accurate diameter."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15,
                accurate_diameter=True
            )
        ]

        # Mock the filter method to return the asteroids
        repo.filter = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.get_asteroids_with_accurate_diameter()

        # Assert
        assert result == expected_asteroids
        repo.filter.assert_called_once_with(
            filters={"accurate_diameter": True},
            skip=0,
            limit=100,
            order_by="estimated_diameter_km"
        )

    @pytest.mark.asyncio
    async def test_get_asteroids_by_orbit_class(self, mock_session):
        """Test getting asteroids by orbit class."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session
        expected_asteroids = [
            AsteroidModel(
                designation="2023 DW",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15,
                orbit_class="Apollo"
            )
        ]

        # Mock the filter method to return the asteroids
        repo.filter = AsyncMock(return_value=expected_asteroids)
        
        # Act
        result = await repo.get_asteroids_by_orbit_class("Apollo")

        # Assert
        assert result == expected_asteroids
        repo.filter.assert_called_once_with(
            filters={"orbit_class": "Apollo"},
            skip=0,
            limit=100,
            order_by="designation"
        )

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, mock_session):
        """Test getting statistics for asteroids."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Mock the SQLAlchemy queries
        mock_execute = AsyncMock()
        mock_scalar = Mock()

        # Set up scalar results for different queries
        scalar_results = [50.0, 0.01, 10, 20, 30, 50]
        scalar_iter = iter(scalar_results)
        mock_scalar.side_effect = lambda: next(scalar_iter)

        mock_execute.return_value.scalar = mock_scalar
        mock_session.execute = mock_execute

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_asteroids"] == 100
        assert result["average_diameter_km"] == 50.0
        assert result["min_earth_moid_au"] == 0.01
        assert result["accurate_diameter_count"] == 10
        assert result["percent_accurate"] == 10.0
        assert result["diameter_source_stats"] == {"measured": 20, "computed": 30, "calculated": 50}
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_get_statistics_empty_database(self, mock_session):
        """Test getting statistics when database is empty."""
        # Arrange
        repo = AsteroidRepository()
        repo.session = mock_session

        # Mock the count method to return 0
        repo.count = AsyncMock(return_value=0)

        # Mock the SQLAlchemy queries to return None or 0
        mock_execute = AsyncMock()
        mock_scalar = Mock()

        # Set up scalar results for different queries (all 0 or None)
        scalar_results = [None, None, 0, None, None, None]
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
        assert result["total_asteroids"] == 0
        assert result["average_diameter_km"] == 0
        assert result["min_earth_moid_au"] == 0
        assert result["accurate_diameter_count"] == 0
        assert result["percent_accurate"] == 0
        assert result["diameter_source_stats"] == {"measured": 0, "computed": 0, "calculated": 0}

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
                "albedo": 0.15
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
        mock_execute = AsyncMock()
        mock_execute.side_effect = Exception("Database error")
        mock_session.execute = mock_execute

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.get_statistics()