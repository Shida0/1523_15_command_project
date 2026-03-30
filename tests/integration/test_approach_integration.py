"""
Integration tests for Approach domain.

These tests use a real in-memory SQLite database to test the repositories
and Unit of Work with actual database operations.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from domains.asteroid.models.asteroid import AsteroidModel
from domains.approach.models.close_approach import CloseApproachModel
from domains.approach.repositories.approach_repository import ApproachRepository
from domains.approach.services.approach_service import ApproachService
from shared.transaction.uow import UnitOfWork


@pytest.fixture(scope="session")
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
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
        # Cleanup - delete all data after test from all tables
        await session.rollback()
        # Import all models to ensure all tables are in metadata
        from domains.approach.models.close_approach import CloseApproachModel
        from domains.threat.models.threat_assessment import ThreatAssessmentModel
        for table in reversed(AsteroidModel.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture
def session_factory(test_engine):
    """Create session factory for services."""
    return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def approach_repository(db_session):
    """Create approach repository with real database session."""
    repo = ApproachRepository()
    repo.session = db_session
    return repo


@pytest.fixture
def approach_service(session_factory):
    """Create approach service with real database."""
    return ApproachService(session_factory)


@pytest.fixture
async def sample_asteroid(db_session):
    """Create a sample asteroid for approach tests."""
    # Clean up any existing data with same designation
    from sqlalchemy import delete
    from domains.approach.models.close_approach import CloseApproachModel
    await db_session.execute(delete(CloseApproachModel).where(CloseApproachModel.asteroid_designation == "2023 TEST"))
    await db_session.execute(delete(AsteroidModel).where(AsteroidModel.designation == "2023 TEST"))
    await db_session.commit()
    
    asteroid = AsteroidModel(
        designation="2023 TEST",
        name="Test Asteroid",
        perihelion_au=0.9,
        aphelion_au=1.5,
        earth_moid_au=0.03,
        absolute_magnitude=20.5,
        estimated_diameter_km=0.15,
        accurate_diameter=False,
        albedo=0.15,
        diameter_source="calculated",
        orbit_class="Apollo"
    )
    db_session.add(asteroid)
    await db_session.commit()
    await db_session.refresh(asteroid)
    return asteroid


@pytest.fixture
def sample_approach_data():
    """Sample approach data template for integration tests."""
    now = datetime.now(timezone.utc)
    return {
        "approach_time": now + timedelta(days=30),
        "distance_au": 0.002,
        "distance_km": 299195.74,
        "velocity_km_s": 10.5,
        "asteroid_designation": "2023 TEST",
        "asteroid_name": "Test Asteroid",
        "data_source": "NASA CAD API",
        "calculation_batch_id": "test_batch"
    }


class TestApproachRepositoryIntegration:
    """Integration tests for ApproachRepository."""

    @pytest.mark.asyncio
    async def test_create_and_get_approach(self, db_session, approach_repository, sample_asteroid, sample_approach_data):
        """Test creating and retrieving an approach."""
        # Arrange
        approach = CloseApproachModel(**sample_approach_data, asteroid_id=sample_asteroid.id)
        db_session.add(approach)
        await db_session.commit()
        await db_session.refresh(approach)

        # Act
        result = await approach_repository.get_by_asteroid(sample_asteroid.id)

        # Assert
        assert len(result) == 1
        assert result[0].asteroid_id == sample_asteroid.id
        assert result[0].distance_au == 0.002

    @pytest.mark.asyncio
    async def test_get_by_asteroid_designation(self, db_session, approach_repository, sample_asteroid, sample_approach_data):
        """Test getting approaches by asteroid designation."""
        # Arrange
        approach = CloseApproachModel(**sample_approach_data, asteroid_id=sample_asteroid.id)
        db_session.add(approach)
        await db_session.commit()

        # Act
        result = await approach_repository.get_by_asteroid_designation("2023 TEST")

        # Assert
        assert len(result) == 1
        assert result[0].asteroid_designation == "2023 TEST"

    @pytest.mark.asyncio
    async def test_get_approaches_in_period(self, db_session, approach_repository, sample_asteroid):
        """Test getting approaches in a time period."""
        # Arrange - Create approaches at different times
        now = datetime.now(timezone.utc)
        approaches = [
            CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i * 30),
                distance_au=0.001 * (i + 1),
                distance_km=149597.87 * (i + 1),
                velocity_km_s=10.0 + i,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            for i in range(6)  # 0, 30, 60, 90, 120, 150 days
        ]
        for approach in approaches:
            db_session.add(approach)
        await db_session.commit()

        # Act - Get approaches in next 90 days
        result = await approach_repository.get_approaches_in_period(
            start_date=now,
            end_date=now + timedelta(days=90),
            skip=0,
            limit=100
        )

        # Assert
        assert len(result) == 4  # Days 0, 30, 60, 90

    @pytest.mark.asyncio
    async def test_get_approaches_in_period_with_max_distance(self, db_session, approach_repository, sample_asteroid):
        """Test getting approaches in period with max distance filter."""
        # Arrange
        now = datetime.now(timezone.utc)
        approaches = [
            CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=30, hours=i),  # Unique timestamps
                distance_au=0.001 * (i + 1),  # 0.001, 0.002, 0.003
                distance_km=149597.87 * (i + 1),
                velocity_km_s=10.0,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            for i in range(3)
        ]
        for approach in approaches:
            db_session.add(approach)
        await db_session.commit()

        # Act - Get approaches within 0.002 AU
        result = await approach_repository.get_approaches_in_period(
            start_date=now,
            end_date=now + timedelta(days=365),
            max_distance=0.002,
            skip=0,
            limit=100
        )

        # Assert
        assert len(result) == 2  # 0.001 and 0.002

    @pytest.mark.asyncio
    async def test_get_upcoming_approaches(self, db_session, approach_repository, sample_asteroid):
        """Test getting upcoming approaches."""
        # Arrange
        now = datetime.now(timezone.utc)
        approaches = [
            CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i * 10),  # 0, 10, 20, 30 days
                distance_au=0.001,
                distance_km=149597.87,
                velocity_km_s=10.0,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            for i in range(4)
        ]
        for approach in approaches:
            db_session.add(approach)
        await db_session.commit()

        # Act
        result = await approach_repository.get_upcoming_approaches(limit=3)

        # Assert
        assert len(result) <= 3
        # All should be in the future
        for approach in result:
            assert approach.approach_time >= now

    @pytest.mark.asyncio
    async def test_get_closest_approaches_by_distance(self, db_session, approach_repository, sample_asteroid):
        """Test getting closest approaches by distance."""
        # Arrange
        now = datetime.now(timezone.utc)
        approaches = [
            CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i),
                distance_au=0.01 - (i * 0.002),  # 0.01, 0.008, 0.006, 0.004, 0.002
                distance_km=1495978.7 * (1 - i * 0.2),
                velocity_km_s=10.0,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            for i in range(5)
        ]
        for approach in approaches:
            db_session.add(approach)
        await db_session.commit()

        # Act
        result = await approach_repository.get_closest_approaches_by_distance(limit=3)

        # Assert
        assert len(result) == 3
        # Should be sorted by distance (closest first)
        assert result[0].distance_au <= result[1].distance_au <= result[2].distance_au

    @pytest.mark.asyncio
    async def test_get_fastest_approaches(self, db_session, approach_repository, sample_asteroid):
        """Test getting fastest approaches."""
        # Arrange
        now = datetime.now(timezone.utc)
        approaches = [
            CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i),
                distance_au=0.005,
                distance_km=747989.35,
                velocity_km_s=8.0 + (i * 2),  # 8, 10, 12, 14, 16 km/s
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            for i in range(5)
        ]
        for approach in approaches:
            db_session.add(approach)
        await db_session.commit()

        # Act
        result = await approach_repository.get_fastest_approaches(limit=3)

        # Assert
        assert len(result) == 3
        # Should be sorted by velocity (fastest first)
        assert result[0].velocity_km_s >= result[1].velocity_km_s >= result[2].velocity_km_s

    @pytest.mark.asyncio
    async def test_pagination_skip_limit(self, db_session, approach_repository, sample_asteroid):
        """Test pagination with skip and limit."""
        # Arrange - Create 10 approaches
        now = datetime.now(timezone.utc)
        for i in range(10):
            approach = CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i),
                distance_au=0.001 * (i + 1),
                distance_km=149597.87 * (i + 1),
                velocity_km_s=10.0,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            db_session.add(approach)
        await db_session.commit()

        # Act - Get first page
        page1 = await approach_repository.get_by_asteroid(
            sample_asteroid.id, skip=0, limit=5
        )
        
        # Act - Get second page
        page2 = await approach_repository.get_by_asteroid(
            sample_asteroid.id, skip=5, limit=5
        )

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        # Ensure no overlap
        page1_ids = {a.id for a in page1}
        page2_ids = {a.id for a in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_get_statistics(self, db_session, approach_repository, sample_asteroid):
        """Test getting statistics from real database."""
        # Arrange
        now = datetime.now(timezone.utc)
        approaches = [
            CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i * 30),
                distance_au=0.001 * (i + 1),
                distance_km=149597.87 * (i + 1),
                velocity_km_s=10.0 + i,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            for i in range(5)
        ]
        for approach in approaches:
            db_session.add(approach)
        await db_session.commit()

        # Act
        stats = await approach_repository.get_statistics()

        # Assert
        assert stats["total_approaches"] == 5
        assert "future_approaches" in stats
        assert "average_distance_au" in stats
        assert "average_velocity_km_s" in stats
        assert "closest_distance_au" in stats

    @pytest.mark.asyncio
    async def test_bulk_create_approaches(self, db_session, approach_repository, sample_asteroid):
        """Test bulk creating approaches."""
        # Arrange
        now = datetime.now(timezone.utc)
        approaches_data = [
            {
                "asteroid_id": sample_asteroid.id,
                "approach_time": now + timedelta(days=i * 30),
                "distance_au": 0.001 * (i + 1),
                "distance_km": 149597.87 * (i + 1),
                "velocity_km_s": 10.0 + i,
                "asteroid_designation": "2023 TEST",
                "data_source": "NASA CAD API"
            }
            for i in range(5)
        ]

        # Act
        result = await approach_repository.bulk_create_approaches(
            approaches_data, "test_batch"
        )

        # Assert
        assert result == 5


class TestApproachServiceIntegration:
    """Integration tests for ApproachService."""

    @pytest.mark.asyncio
    async def test_service_get_by_asteroid_id(self, approach_service, db_session, sample_asteroid):
        """Test service getting approaches by asteroid ID."""
        # Arrange
        now = datetime.now(timezone.utc)
        for i in range(3):
            approach = CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i * 30),
                distance_au=0.001 * (i + 1),
                distance_km=149597.87 * (i + 1),
                velocity_km_s=10.0,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            db_session.add(approach)
        await db_session.commit()

        # Act
        result = await approach_service.get_by_asteroid_id(sample_asteroid.id)

        # Assert
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_service_get_upcoming(self, approach_service, db_session, sample_asteroid):
        """Test service getting upcoming approaches."""
        # Arrange
        now = datetime.now(timezone.utc)
        for i in range(5):
            approach = CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i * 10),
                distance_au=0.001,
                distance_km=149597.87,
                velocity_km_s=10.0,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            db_session.add(approach)
        await db_session.commit()

        # Act
        result = await approach_service.get_upcoming(limit=3)

        # Assert
        assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_service_get_statistics(self, approach_service, db_session, sample_asteroid):
        """Test service getting statistics."""
        # Arrange
        now = datetime.now(timezone.utc)
        for i in range(5):
            approach = CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=i * 30),
                distance_au=0.001 * (i + 1),
                distance_km=149597.87 * (i + 1),
                velocity_km_s=10.0 + i,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            db_session.add(approach)
        await db_session.commit()

        # Act
        stats = await approach_service.get_statistics()

        # Assert
        assert stats["total_approaches"] == 5


class TestApproachUnitOfWorkIntegration:
    """Integration tests for Unit of Work with Approach domain."""

    @pytest.mark.asyncio
    async def test_uow_create_asteroid_and_approach(self, session_factory, sample_asteroid):
        """Test creating asteroid and approach in single transaction."""
        now = datetime.now(timezone.utc)
        
        # Act
        async with UnitOfWork(session_factory) as uow:
            approach = CloseApproachModel(
                asteroid_id=sample_asteroid.id,
                approach_time=now + timedelta(days=30),
                distance_au=0.002,
                distance_km=299195.74,
                velocity_km_s=10.5,
                asteroid_designation="2023 TEST",
                data_source="NASA CAD API"
            )
            uow.session.add(approach)
            await uow.session.commit()
        
        # Assert - Verify approach was persisted
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(CloseApproachModel).where(
                    CloseApproachModel.asteroid_id == sample_asteroid.id
                )
            )
            db_approach = result.scalar_one_or_none()
            assert db_approach is not None
            assert db_approach.distance_au == 0.002
