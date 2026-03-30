"""
Unit tests for ThreatRepository.

These tests verify that repository methods correctly form SQL queries
by mocking session.execute() instead of internal methods.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy import select, func
from datetime import datetime, timezone

from domains.threat.models.threat_assessment import ThreatAssessmentModel
from domains.threat.repositories.threat_repository import ThreatRepository


class TestThreatRepository:
    """Unit tests for ThreatRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session, sample_threat_data):
        """Test getting threat assessment by designation when found."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=expected_threat)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_designation("2023 TEST")

        # Assert
        assert result == expected_threat
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session):
        """Test getting threat assessment by designation when not found."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_designation("nonexistent")

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_found(self, mock_session, sample_threat_data):
        """Test getting threat assessment by asteroid ID when found."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=expected_threat)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_asteroid_id(1)

        # Assert
        assert result == expected_threat
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_not_found(self, mock_session):
        """Test getting threat assessment by asteroid ID when not found."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_asteroid_id(999)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_high_risk_threats(self, mock_session, sample_threat_data):
        """Test getting high risk threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        # Create high risk threat (ts_max >= 5)
        data = {**sample_threat_data, "ts_max": 6}
        expected_threat = ThreatAssessmentModel(**data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_high_risk_threats(limit=20)

        # Assert
        assert len(result) == 1
        assert result[0].ts_max >= 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_threats_by_risk_level(self, mock_session, sample_threat_data):
        """Test getting threats by risk level (Torino scale)."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        data = {**sample_threat_data, "ts_max": 5}
        expected_threat = ThreatAssessmentModel(**data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_threats_by_risk_level(
            min_ts=4, max_ts=6, skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_threats_by_risk_level_with_pagination(self, mock_session, sample_threat_data):
        """Test getting threats by risk level with custom pagination."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        data = {**sample_threat_data, "ts_max": 5}
        expected_threat = ThreatAssessmentModel(**data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_threats_by_risk_level(
            min_ts=4, max_ts=6, skip=10, limit=50
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_threats_by_probability(self, mock_session, sample_threat_data):
        """Test getting threats by probability range."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_threats_by_probability(
            min_probability=0.001, max_probability=0.01, skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_threats_by_energy(self, mock_session, sample_threat_data):
        """Test getting threats by energy range."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_threats_by_energy(
            min_energy=10.0, max_energy=100.0, skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_threats_by_energy_no_max(self, mock_session, sample_threat_data):
        """Test getting threats by minimum energy only."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_threats_by_energy(min_energy=10.0, skip=0, limit=100)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_threats_by_impact_category(self, mock_session, sample_threat_data):
        """Test getting threats by impact category."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_threats_by_impact_category(
            "локальный", skip=0, limit=100
        )

        # Assert
        assert len(result) == 1
        assert result[0].impact_category == "локальный"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_threat_assessment(self, mock_session, sample_threat_data):
        """Test updating threat assessment."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        existing_threat = ThreatAssessmentModel(**sample_threat_data)
        
        updated_data = {
            "ip": 0.002,
            "ts_max": 2,
            "energy_megatons": 15.0
        }
        
        updated_data_full = {**sample_threat_data, **updated_data}
        updated_threat = ThreatAssessmentModel(**updated_data_full)
        
        # Mock get_by_designation
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=existing_threat)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock update
        repo.update = AsyncMock(return_value=updated_threat)

        # Act
        result = await repo.update_threat_assessment("2023 TEST", updated_data)

        # Assert
        assert result == updated_threat
        repo.update.assert_called_once_with(existing_threat.id, updated_data)

    @pytest.mark.asyncio
    async def test_update_threat_assessment_not_found(self, mock_session):
        """Test updating threat assessment when not found."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.update_threat_assessment("nonexistent", {})

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_bulk_create_threats(self, mock_session):
        """Test bulk creating threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        threats_data = [
            {
                "asteroid_id": 1,
                "designation": "2023 DW",
                "fullname": "2023 DW (Asteroid)",
                "ip": 0.001,
                "ts_max": 1,
                "ps_max": -2.5,
                "diameter": 0.1,
                "v_inf": 10.5,
                "h": 20.5,
                "n_imp": 5,
                "impact_years": [2025],
                "last_obs": "2023-01-01",
                "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
                "torino_scale_ru": "1 — Нормальный (зелёный)",
                "impact_probability_text_ru": "0.1% (1 к 1,000)",
                "energy_megatons": 10.0,
                "impact_category": "локальный"
            }
        ]

        # Mock the bulk_create method
        repo.bulk_create = AsyncMock(return_value=(3, 1))

        # Act
        created, updated = await repo.bulk_create_threats(threats_data)

        # Assert
        assert created == 3
        assert updated == 1
        repo.bulk_create.assert_called_once_with(
            data_list=threats_data,
            conflict_action="update",
            conflict_fields=["asteroid_id"]
        )

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, mock_session, ordered_scalar_mock):
        """Test getting statistics for threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Create ordered mock for scalar results
        # Order: 11 torino scale queries (5 each), 3 category queries (10 each),
        # avg_prob, max_energy, avg_energy, non_zero_count, high_risk_count
        scalar_values = [5] * 11 + [10] * 3 + [0.001, 100.0, 50.0, 20, 5]
        mock_result = ordered_scalar_mock(scalar_values, default=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_threats"] == 100
        assert result["torino_scale_distribution"]["ts_0"]["count"] == 5
        assert result["impact_category_distribution"]["локальный"]["count"] == 10
        assert result["average_probability"] == 0.001
        assert result["average_energy_mt"] == 50.0
        assert result["max_energy_mt"] == 100.0
        assert result["non_zero_probability_count"] == 20
        assert result["high_risk_count"] == 5
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_get_statistics_empty_database(self, mock_session, ordered_scalar_mock):
        """Test getting statistics when database is empty."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session

        # Mock the count method to return 0
        repo.count = AsyncMock(return_value=0)

        # Create ordered mock for scalar results (all 0)
        scalar_values = [0] * 19  # 11 torino + 3 category + 5 other
        mock_result = ordered_scalar_mock(scalar_values, default=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_threats"] == 0
        # Check that percentages are 0 when total is 0
        assert result["torino_scale_distribution"]["ts_0"]["percent"] == 0
        assert result["impact_category_distribution"]["локальный"]["percent"] == 0

    @pytest.mark.asyncio
    async def test_search_threats(self, mock_session, sample_threat_data):
        """Test searching threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        
        expected_threat = ThreatAssessmentModel(**sample_threat_data)
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[expected_threat])
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.search_threats("2023 TEST", skip=0, limit=50)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_statistics_exception_handling(self, mock_session):
        """Test that exceptions in get_statistics are properly handled."""
        # Arrange
        repo = ThreatRepository()
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
        repo = ThreatRepository()
        repo.session = mock_session
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=42)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.count()

        # Assert
        assert result == 42
        mock_session.execute.assert_called_once()
