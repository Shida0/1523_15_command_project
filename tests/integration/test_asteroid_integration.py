"""
Integration tests for Asteroid domain.

These tests use a real in-memory SQLite database to test the repositories
and Unit of Work with actual database operations.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from domains.asteroid.models.asteroid import AsteroidModel
from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
from domains.asteroid.services.asteroid_service import AsteroidService
from shared.transaction.uow import UnitOfWork


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite engine for integration tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    # Create tables
    import asyncio
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(AsteroidModel.metadata.create_all)
    asyncio.get_event_loop().run_until_complete(create_tables())
    
    yield engine
    # Cleanup
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture
async def db_session(test_engine):
    """Create database tables and session for integration tests."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(AsteroidModel.metadata.create_all)
    
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
        # Cleanup - delete all data after test
        # Import all models to ensure all tables are in metadata
        from domains.approach.models.close_approach import CloseApproachModel
        from domains.threat.models.threat_assessment import ThreatAssessmentModel
        await session.rollback()
        for table in reversed(AsteroidModel.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
    
    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(AsteroidModel.metadata.drop_all)


@pytest.fixture
def session_factory(test_engine):
    """Create session factory for services."""
    return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def asteroid_repository(db_session):
    """Create asteroid repository with real database session."""
    repo = AsteroidRepository()
    repo.session = db_session
    return repo


@pytest.fixture
def asteroid_service(session_factory):
    """Create asteroid service with real database."""
    return AsteroidService(session_factory)


@pytest.fixture
def sample_asteroid_data():
    """Sample asteroid data for integration tests."""
    return {
        "designation": "2023 TEST",
        "name": "Test Asteroid",
        "perihelion_au": 0.9,
        "aphelion_au": 1.5,
        "earth_moid_au": 0.03,
        "absolute_magnitude": 20.5,
        "estimated_diameter_km": 0.15,
        "accurate_diameter": False,
        "albedo": 0.15,
        "diameter_source": "calculated",
        "orbit_id": "test_orbit",
        "orbit_class": "Apollo"
    }


class TestAsteroidRepositoryIntegration:
    """Integration tests for AsteroidRepository."""

    @pytest.mark.asyncio
    async def test_create_and_get_asteroid(self, db_session, asteroid_repository, sample_asteroid_data):
        """Test creating and retrieving an asteroid."""
        # Arrange
        asteroid = AsteroidModel(**sample_asteroid_data)
        db_session.add(asteroid)
        await db_session.commit()
        await db_session.refresh(asteroid)

        # Act
        result = await asteroid_repository.get_by_designation("2023 TEST")

        # Assert
        assert result is not None
        assert result.designation == "2023 TEST"
        assert result.name == "Test Asteroid"
        assert result.earth_moid_au == 0.03

    @pytest.mark.asyncio
    async def test_get_asteroid_not_found(self, asteroid_repository):
        """Test getting a non-existent asteroid."""
        # Act
        result = await asteroid_repository.get_by_designation("NONEXISTENT")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_asteroids_by_earth_moid(self, db_session, asteroid_repository):
        """Test filtering asteroids by MOID."""
        # Arrange - Create multiple asteroids with different MOIDs
        asteroids = [
            AsteroidModel(
                designation=f"AST{i}",
                name=f"Asteroid {i}",
                earth_moid_au=0.01 * (i + 1),  # 0.01, 0.02, 0.03, 0.04, 0.05
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            for i in range(5)
        ]
        for asteroid in asteroids:
            db_session.add(asteroid)
        await db_session.commit()

        # Act
        result = await asteroid_repository.get_asteroids_by_earth_moid(0.03)

        # Assert
        assert len(result) == 3  # MOID <= 0.03: 0.01, 0.02, 0.03
        for asteroid in result:
            assert asteroid.earth_moid_au <= 0.03

    @pytest.mark.asyncio
    async def test_get_asteroids_by_orbit_class(self, db_session, asteroid_repository):
        """Test filtering asteroids by orbit class."""
        # Arrange
        asteroids = [
            AsteroidModel(
                designation="APOLLO1",
                orbit_class="Apollo",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            ),
            AsteroidModel(
                designation="ATEN1",
                orbit_class="Aten",
                earth_moid_au=0.02,
                absolute_magnitude=21.0,
                estimated_diameter_km=0.2,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            ),
            AsteroidModel(
                designation="APOLLO2",
                orbit_class="Apollo",
                earth_moid_au=0.03,
                absolute_magnitude=22.0,
                estimated_diameter_km=0.3,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
        ]
        for asteroid in asteroids:
            db_session.add(asteroid)
        await db_session.commit()

        # Act
        result = await asteroid_repository.get_asteroids_by_orbit_class("Apollo")

        # Assert
        assert len(result) == 2
        for asteroid in result:
            assert asteroid.orbit_class == "Apollo"

    @pytest.mark.asyncio
    async def test_get_asteroids_with_accurate_diameter(self, db_session, asteroid_repository):
        """Test getting asteroids with accurate diameter."""
        # Arrange
        asteroids = [
            AsteroidModel(
                designation="ACCURATE1",
                orbit_class="Apollo",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=True,
                albedo=0.15,
                diameter_source="measured"
            ),
            AsteroidModel(
                designation="NOTACCURATE1",
                orbit_class="Aten",
                earth_moid_au=0.02,
                absolute_magnitude=21.0,
                estimated_diameter_km=0.2,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
        ]
        for asteroid in asteroids:
            db_session.add(asteroid)
        await db_session.commit()

        # Act
        result = await asteroid_repository.get_asteroids_with_accurate_diameter()

        # Assert
        assert len(result) == 1
        assert result[0].accurate_diameter is True
        assert result[0].designation == "ACCURATE1"

    @pytest.mark.asyncio
    async def test_pagination_skip_limit(self, db_session, asteroid_repository):
        """Test pagination with skip and limit."""
        # Arrange - Create 10 asteroids
        for i in range(10):
            asteroid = AsteroidModel(
                designation=f"AST{i:03d}",
                orbit_class="Apollo",
                earth_moid_au=0.01 * i,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            db_session.add(asteroid)
        await db_session.commit()

        # Act - Get first page
        page1 = await asteroid_repository.get_asteroids_by_orbit_class(
            "Apollo", skip=0, limit=5
        )
        
        # Act - Get second page
        page2 = await asteroid_repository.get_asteroids_by_orbit_class(
            "Apollo", skip=5, limit=5
        )

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        # Ensure no overlap
        page1_ids = {a.designation for a in page1}
        page2_ids = {a.designation for a in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_get_statistics(self, db_session, asteroid_repository):
        """Test getting statistics from real database."""
        # Arrange - Create test data
        asteroids = [
            AsteroidModel(
                designation=f"STAT{i}",
                orbit_class="Apollo" if i % 2 == 0 else "Aten",
                earth_moid_au=0.01 * (i + 1),
                absolute_magnitude=20.0 + i,
                estimated_diameter_km=0.1 * (i + 1),
                accurate_diameter=(i % 3 == 0),
                albedo=0.15,
                diameter_source="measured" if i % 3 == 0 else "calculated"
            )
            for i in range(10)
        ]
        for asteroid in asteroids:
            db_session.add(asteroid)
        await db_session.commit()

        # Act
        stats = await asteroid_repository.get_statistics()

        # Assert
        assert stats["total_asteroids"] == 10
        assert stats["accurate_diameter_count"] == 4  # i=0,3,6,9
        assert "average_diameter_km" in stats
        assert "min_earth_moid_au" in stats
        assert "diameter_source_stats" in stats

    @pytest.mark.asyncio
    async def test_bulk_create_asteroids(self, db_session, asteroid_repository):
        """Test bulk creating asteroids."""
        # Arrange
        asteroids_data = [
            {
                "designation": f"BULK{i}",
                "name": f"Bulk Asteroid {i}",
                "orbit_class": "Apollo",
                "earth_moid_au": 0.01 * i,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.1,
                "accurate_diameter": False,
                "albedo": 0.15,
                "diameter_source": "calculated"
            }
            for i in range(5)
        ]

        # Act
        created, updated = await asteroid_repository.bulk_create_asteroids(asteroids_data)

        # Assert
        assert created == 5
        assert updated == 0


class TestAsteroidServiceIntegration:
    """Integration tests for AsteroidService."""

    @pytest.mark.asyncio
    async def test_service_get_by_designation(self, asteroid_service, db_session, sample_asteroid_data):
        """Test service getting asteroid by designation."""
        # Arrange - Create asteroid directly in DB
        asteroid = AsteroidModel(**sample_asteroid_data)
        db_session.add(asteroid)
        await db_session.commit()

        # Act
        result = await asteroid_service.get_by_designation("2023 TEST")

        # Assert
        assert result is not None
        assert result["designation"] == "2023 TEST"

    @pytest.mark.asyncio
    async def test_service_get_by_moid_with_pagination(self, asteroid_service, db_session):
        """Test service getting asteroids by MOID with pagination."""
        # Arrange
        for i in range(10):
            asteroid = AsteroidModel(
                designation=f"MOID{i}",
                earth_moid_au=0.01 * (i + 1),
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            db_session.add(asteroid)
        await db_session.commit()

        # Act - Get first page
        page1 = await asteroid_service.get_by_moid(0.1, skip=0, limit=5)
        
        # Act - Get second page
        page2 = await asteroid_service.get_by_moid(0.1, skip=5, limit=5)

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5

    @pytest.mark.asyncio
    async def test_service_get_statistics(self, asteroid_service, db_session):
        """Test service getting statistics."""
        # Arrange
        for i in range(5):
            asteroid = AsteroidModel(
                designation=f"STAT{i}",
                orbit_class="Apollo",
                earth_moid_au=0.01 * (i + 1),
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1 * (i + 1),
                accurate_diameter=(i % 2 == 0),
                albedo=0.15,
                diameter_source="calculated"
            )
            db_session.add(asteroid)
        await db_session.commit()

        # Act
        stats = await asteroid_service.get_statistics()

        # Assert
        assert stats["total_asteroids"] == 5
        assert "average_diameter_km" in stats


class TestAsteroidUnitOfWorkIntegration:
    """Integration tests for Unit of Work with Asteroid domain."""

    @pytest.mark.asyncio
    async def test_uow_successful_transaction(self, session_factory, sample_asteroid_data):
        """Test successful transaction through Unit of Work."""
        # Act
        async with UnitOfWork(session_factory) as uow:
            asteroid = AsteroidModel(**sample_asteroid_data)
            uow.session.add(asteroid)
            await uow.session.commit()
        
        # Assert - Verify asteroid was persisted
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "2023 TEST")
            )
            db_asteroid = result.scalar_one_or_none()
            assert db_asteroid is not None
            assert db_asteroid.name == "Test Asteroid"

    @pytest.mark.asyncio
    async def test_uow_rollback_on_error(self, session_factory, sample_asteroid_data):
        """Test transaction rollback on error."""
        # Act - Try to create asteroid but raise error before commit
        try:
            async with UnitOfWork(session_factory) as uow:
                asteroid = AsteroidModel(**sample_asteroid_data)
                uow.session.add(asteroid)
                # Don't commit, just let context manager exit
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Assert - Verify asteroid was NOT persisted
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "2023 TEST")
            )
            db_asteroid = result.scalar_one_or_none()
            assert db_asteroid is None
