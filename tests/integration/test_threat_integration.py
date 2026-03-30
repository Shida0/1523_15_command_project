"""
Integration tests for Threat domain.

These tests use a real in-memory SQLite database to test the repositories
and Unit of Work with actual database operations.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from domains.asteroid.models.asteroid import AsteroidModel
from domains.threat.models.threat_assessment import ThreatAssessmentModel
from domains.threat.repositories.threat_repository import ThreatRepository
from domains.threat.services.threat_service import ThreatService
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
    """Create session factory for services."""
    return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def threat_repository(db_session):
    """Create threat repository with real database session."""
    repo = ThreatRepository()
    repo.session = db_session
    return repo


@pytest.fixture
def threat_service(session_factory):
    """Create threat service with real database."""
    return ThreatService(session_factory)


@pytest.fixture
async def sample_asteroid(db_session):
    """Create a sample asteroid for threat tests."""
    # Clean up any existing asteroid with same designation
    from sqlalchemy import delete
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
def sample_threat_data():
    """Sample threat data template for integration tests."""
    return {
        "designation": "2023 TEST",
        "fullname": "2023 TEST (Test Asteroid)",
        "ip": 0.001,
        "ts_max": 1,
        "ps_max": -2.5,
        "diameter": 0.15,
        "v_inf": 10.5,
        "h": 20.5,
        "n_imp": 3,
        "impact_years": [2024, 2025, 2026],
        "last_obs": "2023-12-01",
        "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
        "torino_scale_ru": "1 — Нормальный (зелёный)",
        "impact_probability_text_ru": "0.1% (1 к 1,000)",
        "energy_megatons": 10.0,
        "impact_category": "локальный"
    }


class TestThreatRepositoryIntegration:
    """Integration tests for ThreatRepository."""

    @pytest.mark.asyncio
    async def test_create_and_get_threat(self, db_session, threat_repository, sample_asteroid, sample_threat_data):
        """Test creating and retrieving a threat assessment."""
        # Arrange
        threat = ThreatAssessmentModel(**sample_threat_data, asteroid_id=sample_asteroid.id)
        db_session.add(threat)
        await db_session.commit()
        await db_session.refresh(threat)

        # Act
        result = await threat_repository.get_by_designation("2023 TEST")

        # Assert
        assert result is not None
        assert result.designation == "2023 TEST"
        assert result.ts_max == 1
        assert result.energy_megatons == 10.0

    @pytest.mark.asyncio
    async def test_get_threat_not_found(self, threat_repository):
        """Test getting a non-existent threat."""
        # Act
        result = await threat_repository.get_by_designation("NONEXISTENT")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id(self, db_session, threat_repository, sample_asteroid, sample_threat_data):
        """Test getting threat by asteroid ID."""
        # Arrange
        threat = ThreatAssessmentModel(**sample_threat_data, asteroid_id=sample_asteroid.id)
        db_session.add(threat)
        await db_session.commit()

        # Act
        result = await threat_repository.get_by_asteroid_id(sample_asteroid.id)

        # Assert
        assert result is not None
        assert result.asteroid_id == sample_asteroid.id

    @pytest.mark.asyncio
    async def test_get_high_risk_threats(self, db_session, threat_repository, sample_asteroid):
        """Test getting high risk threats (ts_max >= 5)."""
        # Arrange - Create threats with different risk levels
        threats = [
            ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"RISK{i}",
                fullname=f"Risk {i}",
                ip=0.01 * (i + 1),
                ts_max=i + 3,  # 3, 4, 5, 6, 7
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            for i in range(5)
        ]
        for threat in threats:
            db_session.add(threat)
        await db_session.commit()

        # Act
        result = await threat_repository.get_high_risk_threats(limit=10)

        # Assert
        assert len(result) == 3  # ts_max 5, 6, 7
        for threat in result:
            assert threat.ts_max >= 5

    @pytest.mark.asyncio
    async def test_get_threats_by_risk_level(self, db_session, threat_repository, sample_asteroid):
        """Test getting threats by Torino scale range."""
        # Arrange
        threats = [
            ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"TS{i}",
                fullname=f"Torino Scale {i}",
                ip=0.001,
                ts_max=i,  # 0, 1, 2, 3, 4, 5
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            for i in range(6)
        ]
        for threat in threats:
            db_session.add(threat)
        await db_session.commit()

        # Act - Get threats with ts_max between 2 and 4
        result = await threat_repository.get_threats_by_risk_level(
            min_ts=2, max_ts=4, skip=0, limit=100
        )

        # Assert
        assert len(result) == 3  # ts_max 2, 3, 4
        for threat in result:
            assert 2 <= threat.ts_max <= 4

    @pytest.mark.asyncio
    async def test_get_threats_by_probability(self, db_session, threat_repository, sample_asteroid):
        """Test getting threats by probability range."""
        # Arrange
        threats = [
            ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"PROB{i}",
                fullname=f"Probability {i}",
                ip=0.001 * (i + 1),  # 0.001, 0.002, 0.003, 0.004, 0.005
                ts_max=1,
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            for i in range(5)
        ]
        for threat in threats:
            db_session.add(threat)
        await db_session.commit()

        # Act - Get threats with probability between 0.002 and 0.004
        result = await threat_repository.get_threats_by_probability(
            min_probability=0.002, max_probability=0.004, skip=0, limit=100
        )

        # Assert
        assert len(result) == 3  # 0.002, 0.003, 0.004

    @pytest.mark.asyncio
    async def test_get_threats_by_energy(self, db_session, threat_repository, sample_asteroid):
        """Test getting threats by energy range."""
        # Arrange
        threats = [
            ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"EN{i}",
                fullname=f"Energy {i}",
                ip=0.001,
                ts_max=1,
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0 * (i + 1),  # 10, 20, 30, 40, 50
                impact_category="локальный"
            )
            for i in range(5)
        ]
        for threat in threats:
            db_session.add(threat)
        await db_session.commit()

        # Act - Get threats with energy between 20 and 40 Mt
        result = await threat_repository.get_threats_by_energy(
            min_energy=20.0, max_energy=40.0, skip=0, limit=100
        )

        # Assert
        assert len(result) == 3  # 20, 30, 40

    @pytest.mark.asyncio
    async def test_get_threats_by_impact_category(self, db_session, threat_repository, sample_asteroid):
        """Test getting threats by impact category."""
        # Arrange
        categories = ["локальный", "региональный", "глобальный", "локальный", "региональный"]
        threats = []
        for i, category in enumerate(categories):
            threat = ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"CAT{i}",
                fullname=f"Category {i}",
                ip=0.001,
                ts_max=1,
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category=category
            )
            threats.append(threat)
            db_session.add(threat)
        await db_session.commit()

        # Act - Get threats with "локальный" category
        result = await threat_repository.get_threats_by_impact_category(
            "локальный", skip=0, limit=100
        )

        # Assert
        assert len(result) == 2
        for threat in result:
            assert threat.impact_category == "локальный"

    @pytest.mark.asyncio
    async def test_update_threat_assessment(self, db_session, threat_repository, sample_asteroid, sample_threat_data):
        """Test updating a threat assessment."""
        # Arrange
        threat = ThreatAssessmentModel(**sample_threat_data, asteroid_id=sample_asteroid.id)
        db_session.add(threat)
        await db_session.commit()

        # Act
        updated_data = {
            "ip": 0.002,
            "ts_max": 2,
            "energy_megatons": 15.0
        }
        result = await threat_repository.update_threat_assessment("2023 TEST", updated_data)

        # Assert
        assert result is not None
        assert result.ip == 0.002
        assert result.ts_max == 2
        assert result.energy_megatons == 15.0

    @pytest.mark.asyncio
    async def test_update_threat_assessment_not_found(self, threat_repository):
        """Test updating a non-existent threat."""
        # Act
        result = await threat_repository.update_threat_assessment(
            "NONEXISTENT", {"ip": 0.002}
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_pagination_skip_limit(self, db_session, threat_repository, sample_asteroid):
        """Test pagination with skip and limit."""
        # Arrange - Create 10 threats
        for i in range(10):
            threat = ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"THREAT{i:03d}",
                fullname=f"Threat {i}",
                ip=0.001 * (i + 1),
                ts_max=i % 11,
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            db_session.add(threat)
        await db_session.commit()

        # Act - Get first page
        page1 = await threat_repository.get_threats_by_risk_level(
            min_ts=0, max_ts=10, skip=0, limit=5
        )
        
        # Act - Get second page
        page2 = await threat_repository.get_threats_by_risk_level(
            min_ts=0, max_ts=10, skip=5, limit=5
        )

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        # Ensure no overlap
        page1_ids = {t.designation for t in page1}
        page2_ids = {t.designation for t in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_get_statistics(self, db_session, threat_repository, sample_asteroid):
        """Test getting statistics from real database."""
        # Arrange - Create threats with different Torino scales
        for i in range(10):
            threat = ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"STAT{i}",
                fullname=f"Stat {i}",
                ip=0.001 * (i + 1),
                ts_max=i % 5,  # 0, 1, 2, 3, 4, 0, 1, 2, 3, 4
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0 * (i + 1),
                impact_category="локальный" if i % 2 == 0 else "региональный"
            )
            db_session.add(threat)
        await db_session.commit()

        # Act
        stats = await threat_repository.get_statistics()

        # Assert
        assert stats["total_threats"] == 10
        assert "torino_scale_distribution" in stats
        assert "impact_category_distribution" in stats
        assert "average_probability" in stats
        assert "average_energy_mt" in stats
        assert "max_energy_mt" in stats
        assert "high_risk_count" in stats

    @pytest.mark.asyncio
    async def test_search_threats(self, db_session, threat_repository, sample_asteroid):
        """Test searching threats."""
        # Arrange
        threats = [
            ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"SEARCH{i}",
                fullname=f"Search Target {i}",
                ip=0.001,
                ts_max=1,
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            for i in range(3)
        ]
        for threat in threats:
            db_session.add(threat)
        await db_session.commit()

        # Act
        result = await threat_repository.search_threats("Search", skip=0, limit=50)

        # Assert
        assert len(result) == 3


class TestThreatServiceIntegration:
    """Integration tests for ThreatService."""

    @pytest.mark.asyncio
    async def test_service_get_by_designation(self, threat_service, db_session, sample_asteroid, sample_threat_data):
        """Test service getting threat by designation."""
        # Arrange
        threat = ThreatAssessmentModel(**sample_threat_data, asteroid_id=sample_asteroid.id)
        db_session.add(threat)
        await db_session.commit()

        # Act
        result = await threat_service.get_by_designation("2023 TEST")

        # Assert
        assert result is not None
        assert result["designation"] == "2023 TEST"

    @pytest.mark.asyncio
    async def test_service_get_high_risk(self, threat_service, db_session, sample_asteroid):
        """Test service getting high risk threats."""
        # Arrange
        for i in range(5):
            threat = ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"HIGH{i}",
                fullname=f"High Risk {i}",
                ip=0.01,
                ts_max=i + 4,  # 4, 5, 6, 7, 8
                ps_max=-1.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            db_session.add(threat)
        await db_session.commit()

        # Act
        result = await threat_service.get_high_risk(limit=10)

        # Assert
        assert len(result) == 4  # ts_max 5, 6, 7, 8

    @pytest.mark.asyncio
    async def test_service_get_by_risk_level_with_pagination(self, threat_service, db_session, sample_asteroid):
        """Test service getting threats by risk level with pagination."""
        # Arrange
        for i in range(10):
            threat = ThreatAssessmentModel(
                asteroid_id=sample_asteroid.id + i,
                designation=f"RISK{i}",
                fullname=f"Risk {i}",
                ip=0.001,
                ts_max=i % 6,  # 0-5
                ps_max=-2.0,
                diameter=0.1,
                v_inf=10.0,
                h=20.0,
                n_imp=1,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="TEST",
                torino_scale_ru="TEST",
                impact_probability_text_ru="TEST",
                energy_megatons=10.0,
                impact_category="локальный"
            )
            db_session.add(threat)
        await db_session.commit()

        # Act - Get first page
        page1 = await threat_service.get_by_risk_level(
            min_ts=0, max_ts=5, skip=0, limit=5
        )
        
        # Act - Get second page
        page2 = await threat_service.get_by_risk_level(
            min_ts=0, max_ts=5, skip=5, limit=5
        )

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5


class TestThreatUnitOfWorkIntegration:
    """Integration tests for Unit of Work with Threat domain."""

    @pytest.mark.asyncio
    async def test_uow_create_threat(self, session_factory, sample_asteroid, sample_threat_data):
        """Test creating threat through Unit of Work."""
        # Act
        async with UnitOfWork(session_factory) as uow:
            threat = ThreatAssessmentModel(**sample_threat_data, asteroid_id=sample_asteroid.id)
            uow.session.add(threat)
            await uow.session.commit()
        
        # Assert - Verify threat was persisted
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ThreatAssessmentModel).where(
                    ThreatAssessmentModel.designation == "2023 TEST"
                )
            )
            db_threat = result.scalar_one_or_none()
            assert db_threat is not None
            assert db_threat.ts_max == 1

    @pytest.mark.asyncio
    async def test_uow_rollback_on_error(self, session_factory, sample_asteroid, sample_threat_data):
        """Test transaction rollback on error."""
        # Act - Try to create threat but raise error
        try:
            async with UnitOfWork(session_factory) as uow:
                threat = ThreatAssessmentModel(**sample_threat_data, asteroid_id=sample_asteroid.id)
                uow.session.add(threat)
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Assert - Verify threat was NOT persisted
        async with session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ThreatAssessmentModel).where(
                    ThreatAssessmentModel.designation == "2023 TEST"
                )
            )
            db_threat = result.scalar_one_or_none()
            assert db_threat is None
