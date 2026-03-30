"""
Integration tests for Unit of Work and transactions.

These tests verify that transactions work correctly across multiple domains,
including commit, rollback, and nested operations.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from domains.asteroid.models.asteroid import AsteroidModel
from domains.approach.models.close_approach import CloseApproachModel
from domains.threat.models.threat_assessment import ThreatAssessmentModel
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
        # Cleanup - delete all data after test
        # Import all models to ensure all tables are in metadata
        from domains.approach.models.close_approach import CloseApproachModel
        from domains.threat.models.threat_assessment import ThreatAssessmentModel
        await session.rollback()
        for table in reversed(AsteroidModel.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture
def session_factory(test_engine):
    """Create async session factory."""
    return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


class TestUnitOfWorkTransactions:
    """Tests for Unit of Work transaction management."""

    @pytest.mark.asyncio
    async def test_uow_commit_persists_all_changes(self, session_factory):
        """Test that committing a UoW persists all changes."""
        # Arrange & Act
        async with UnitOfWork(session_factory) as uow:
            asteroid = AsteroidModel(
                designation="COMMIT_TEST",
                name="Commit Test",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            uow.session.add(asteroid)
            await uow.session.commit()
        
        # Assert - Verify outside of UoW context
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "COMMIT_TEST")
            )
            db_asteroid = result.scalar_one_or_none()
            assert db_asteroid is not None
            assert db_asteroid.name == "Commit Test"

    @pytest.mark.asyncio
    async def test_uow_rollback_on_exception(self, session_factory):
        """Test that UoW rolls back on exception."""
        # Arrange & Act
        try:
            async with UnitOfWork(session_factory) as uow:
                asteroid = AsteroidModel(
                    designation="ROLLBACK_TEST",
                    name="Rollback Test",
                    earth_moid_au=0.01,
                    absolute_magnitude=20.0,
                    estimated_diameter_km=0.1,
                    accurate_diameter=False,
                    albedo=0.15,
                    diameter_source="calculated"
                )
                uow.session.add(asteroid)
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Assert - Verify rollback
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "ROLLBACK_TEST")
            )
            db_asteroid = result.scalar_one_or_none()
            assert db_asteroid is None

    @pytest.mark.asyncio
    async def test_uow_multiple_operations_atomic(self, session_factory):
        """Test that multiple operations in UoW are atomic."""
        # Arrange & Act
        try:
            async with UnitOfWork(session_factory) as uow:
                # Create first asteroid
                asteroid1 = AsteroidModel(
                    designation="ATOMIC1",
                    name="Atomic 1",
                    earth_moid_au=0.01,
                    absolute_magnitude=20.0,
                    estimated_diameter_km=0.1,
                    accurate_diameter=False,
                    albedo=0.15,
                    diameter_source="calculated"
                )
                uow.session.add(asteroid1)
                
                # Create second asteroid
                asteroid2 = AsteroidModel(
                    designation="ATOMIC2",
                    name="Atomic 2",
                    earth_moid_au=0.02,
                    absolute_magnitude=21.0,
                    estimated_diameter_km=0.2,
                    accurate_diameter=False,
                    albedo=0.15,
                    diameter_source="calculated"
                )
                uow.session.add(asteroid2)
                
                # Raise error after adding both
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Assert - Both should be rolled back
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AsteroidModel).where(
                    AsteroidModel.designation.in_(["ATOMIC1", "ATOMIC2"])
                )
            )
            db_asteroids = result.scalars().all()
            assert len(db_asteroids) == 0

    @pytest.mark.asyncio
    async def test_uow_repositories_available_in_context(self, session_factory):
        """Test that repositories are available within UoW context."""
        async with UnitOfWork(session_factory) as uow:
            # Assert - Repositories should be available
            assert uow.asteroid_repo is not None
            assert uow.approach_repo is not None
            assert uow.threat_repo is not None
            
            # Assert - Repositories should have session
            assert uow.asteroid_repo.session is not None
            assert uow.approach_repo.session is not None
            assert uow.threat_repo.session is not None


class TestCrossDomainTransactions:
    """Tests for transactions spanning multiple domains."""

    @pytest.mark.asyncio
    async def test_create_asteroid_and_approach_in_transaction(self, session_factory):
        """Test creating asteroid and approach in same transaction."""
        async with UnitOfWork(session_factory) as uow:
            # Create asteroid
            asteroid = AsteroidModel(
                designation="CROSS1",
                name="Cross Domain 1",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            uow.session.add(asteroid)
            await uow.session.flush()  # Get the ID
            
            # Create approach for the asteroid
            approach = CloseApproachModel(
                asteroid_id=asteroid.id,
                approach_time=datetime.now(timezone.utc) + timedelta(days=30),
                distance_au=0.002,
                distance_km=299195.74,
                velocity_km_s=10.5,
                asteroid_designation="CROSS1",
                data_source="NASA CAD API"
            )
            uow.session.add(approach)
            
            await uow.session.commit()
        
        # Assert - Both should be persisted
        async with session_factory() as session:
            from sqlalchemy import select
            asteroid_result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "CROSS1")
            )
            db_asteroid = asteroid_result.scalar_one_or_none()
            assert db_asteroid is not None
            
            approach_result = await session.execute(
                select(CloseApproachModel).where(
                    CloseApproachModel.asteroid_id == db_asteroid.id
                )
            )
            db_approach = approach_result.scalar_one_or_none()
            assert db_approach is not None
            assert db_approach.distance_au == 0.002

    @pytest.mark.asyncio
    async def test_create_full_chain_in_transaction(self, session_factory):
        """Test creating asteroid, approach, and threat in same transaction."""
        async with UnitOfWork(session_factory) as uow:
            # Create asteroid
            asteroid = AsteroidModel(
                designation="FULL_CHAIN",
                name="Full Chain Test",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            uow.session.add(asteroid)
            await uow.session.flush()
            
            # Create approach
            approach = CloseApproachModel(
                asteroid_id=asteroid.id,
                approach_time=datetime.now(timezone.utc) + timedelta(days=30),
                distance_au=0.002,
                distance_km=299195.74,
                velocity_km_s=10.5,
                asteroid_designation="FULL_CHAIN",
                data_source="NASA CAD API"
            )
            uow.session.add(approach)
            
            # Create threat assessment
            threat = ThreatAssessmentModel(
                asteroid_id=asteroid.id,
                designation="FULL_CHAIN",
                fullname="Full Chain Test",
                ip=0.001,
                ts_max=1,
                ps_max=-2.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ",
                torino_scale_ru="1 — Нормальный",
                impact_probability_text_ru="0.1%",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            uow.session.add(threat)
            
            await uow.session.commit()
        
        # Assert - All three should be persisted
        async with session_factory() as session:
            from sqlalchemy import select
            # Check asteroid
            asteroid_result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "FULL_CHAIN")
            )
            db_asteroid = asteroid_result.scalar_one_or_none()
            assert db_asteroid is not None
            
            # Check approach
            approach_result = await session.execute(
                select(CloseApproachModel).where(
                    CloseApproachModel.asteroid_id == db_asteroid.id
                )
            )
            db_approach = approach_result.scalar_one_or_none()
            assert db_approach is not None
            
            # Check threat
            threat_result = await session.execute(
                select(ThreatAssessmentModel).where(
                    ThreatAssessmentModel.asteroid_id == db_asteroid.id
                )
            )
            db_threat = threat_result.scalar_one_or_none()
            assert db_threat is not None
            assert db_threat.ts_max == 1

    @pytest.mark.asyncio
    async def test_partial_failure_rolls_back_all(self, session_factory):
        """Test that partial failure rolls back all changes."""
        try:
            async with UnitOfWork(session_factory) as uow:
                # Create asteroid
                asteroid = AsteroidModel(
                    designation="PARTIAL_FAIL",
                    name="Partial Fail",
                    earth_moid_au=0.01,
                    absolute_magnitude=20.0,
                    estimated_diameter_km=0.1,
                    accurate_diameter=False,
                    albedo=0.15,
                    diameter_source="calculated"
                )
                uow.session.add(asteroid)
                await uow.session.flush()
                
                # Create approach
                approach = CloseApproachModel(
                    asteroid_id=asteroid.id,
                    approach_time=datetime.now(timezone.utc) + timedelta(days=30),
                    distance_au=0.002,
                    distance_km=299195.74,
                    velocity_km_s=10.5,
                    asteroid_designation="PARTIAL_FAIL",
                    data_source="NASA CAD API"
                )
                uow.session.add(approach)
                
                # Simulate failure before threat creation
                raise ValueError("Simulated failure")
        except ValueError:
            pass
        
        # Assert - Nothing should be persisted
        async with session_factory() as session:
            from sqlalchemy import select
            asteroid_result = await session.execute(
                select(AsteroidModel).where(AsteroidModel.designation == "PARTIAL_FAIL")
            )
            db_asteroid = asteroid_result.scalar_one_or_none()
            assert db_asteroid is None


class TestRepositoryOperationsInUoW:
    """Tests for using repositories within Unit of Work."""

    @pytest.mark.asyncio
    async def test_use_asteroid_repo_in_uow(self, session_factory):
        """Test using asteroid repository within UoW."""
        async with UnitOfWork(session_factory) as uow:
            # Create asteroid using repository
            asteroid_data = {
                "designation": "UOW_REPO_TEST",
                "name": "UoW Repo Test",
                "earth_moid_au": 0.01,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.1,
                "accurate_diameter": False,
                "albedo": 0.15,
                "diameter_source": "calculated"
            }
            
            asteroid = AsteroidModel(**asteroid_data)
            uow.session.add(asteroid)
            await uow.session.commit()
            
            # Use repository to retrieve
            retrieved = await uow.asteroid_repo.get_by_designation("UOW_REPO_TEST")
            
            assert retrieved is not None
            assert retrieved.name == "UoW Repo Test"

    @pytest.mark.asyncio
    async def test_use_approach_repo_in_uow(self, session_factory):
        """Test using approach repository within UoW."""
        async with UnitOfWork(session_factory) as uow:
            # Create asteroid first
            asteroid = AsteroidModel(
                designation="APPROACH_REPO",
                name="Approach Repo Test",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            uow.session.add(asteroid)
            await uow.session.flush()
            
            # Create approach
            approach = CloseApproachModel(
                asteroid_id=asteroid.id,
                approach_time=datetime.now(timezone.utc) + timedelta(days=30),
                distance_au=0.002,
                distance_km=299195.74,
                velocity_km_s=10.5,
                asteroid_designation="APPROACH_REPO",
                data_source="NASA CAD API"
            )
            uow.session.add(approach)
            await uow.session.commit()
            
            # Use repository to retrieve
            approaches = await uow.approach_repo.get_by_asteroid(asteroid.id)
            
            assert len(approaches) == 1
            assert approaches[0].distance_au == 0.002

    @pytest.mark.asyncio
    async def test_use_threat_repo_in_uow(self, session_factory):
        """Test using threat repository within UoW."""
        async with UnitOfWork(session_factory) as uow:
            # Create asteroid first
            asteroid = AsteroidModel(
                designation="THREAT_REPO",
                name="Threat Repo Test",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            uow.session.add(asteroid)
            await uow.session.flush()
            
            # Create threat
            threat = ThreatAssessmentModel(
                asteroid_id=asteroid.id,
                designation="THREAT_REPO",
                fullname="Threat Repo Test",
                ip=0.001,
                ts_max=1,
                ps_max=-2.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ",
                torino_scale_ru="1 — Нормальный",
                impact_probability_text_ru="0.1%",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            uow.session.add(threat)
            await uow.session.commit()
            
            # Use repository to retrieve
            retrieved = await uow.threat_repo.get_by_designation("THREAT_REPO")
            
            assert retrieved is not None
            assert retrieved.ts_max == 1


class TestIsolationAndConcurrency:
    """Tests for transaction isolation."""

    @pytest.mark.asyncio
    async def test_uncommitted_changes_not_visible_outside_transaction(self, session_factory):
        """Test that uncommitted changes are not visible outside transaction."""
        # Start first transaction but don't commit
        async with UnitOfWork(session_factory) as uow1:
            asteroid = AsteroidModel(
                designation="ISOLATION_TEST",
                name="Isolation Test",
                earth_moid_au=0.01,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.1,
                accurate_diameter=False,
                albedo=0.15,
                diameter_source="calculated"
            )
            uow1.session.add(asteroid)
            # Don't commit yet
            
            # Try to read from another session
            async with session_factory() as session2:
                from sqlalchemy import select
                result = await session2.execute(
                    select(AsteroidModel).where(
                        AsteroidModel.designation == "ISOLATION_TEST"
                    )
                )
                db_asteroid = result.scalar_one_or_none()
                # Should be None because first transaction hasn't committed
                assert db_asteroid is None
            
            # Now commit
            await uow1.session.commit()
        
        # After commit, should be visible
        async with session_factory() as session3:
            from sqlalchemy import select
            result = await session3.execute(
                select(AsteroidModel).where(
                    AsteroidModel.designation == "ISOLATION_TEST"
                )
            )
            db_asteroid = result.scalar_one_or_none()
            assert db_asteroid is not None
