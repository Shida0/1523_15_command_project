"""
Unit tests for ThreatService.

These tests verify that service methods correctly pass pagination parameters
to repository methods.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from domains.threat.services.threat_service import ThreatService


class TestThreatService:
    """Unit tests for ThreatService class."""

    def test_threat_service_initialization(self, mock_session_factory):
        """Test initializing the threat service."""
        # Arrange & Act
        service = ThreatService(mock_session_factory)

        # Assert
        assert service.session_factory == mock_session_factory

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session_factory):
        """Test getting threat assessment by designation when found."""
        # Arrange
        service = ThreatService(mock_session_factory)
        
        # Mock _model_to_dict to return simple dict
        service._model_to_dict = Mock(return_value={"designation": "2023 TEST", "ts_max": 1})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_by_designation = AsyncMock(return_value=mock_threat)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("2023 TEST")

            # Assert
            assert result is not None
            assert result["designation"] == "2023 TEST"
            mock_uow.threat_repo.get_by_designation.assert_called_once_with("2023 TEST")

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session_factory):
        """Test getting threat assessment by designation when not found."""
        # Arrange
        service = ThreatService(mock_session_factory)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo.get_by_designation = AsyncMock(return_value=None)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("nonexistent")

            # Assert
            assert result is None
            mock_uow.threat_repo.get_by_designation.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_found(self, mock_session_factory):
        """Test getting threat assessment by asteroid ID when found."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"asteroid_id": 1, "ts_max": 1})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_by_asteroid_id = AsyncMock(return_value=mock_threat)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(1)

            # Assert
            assert result is not None
            assert result["asteroid_id"] == 1
            mock_uow.threat_repo.get_by_asteroid_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_not_found(self, mock_session_factory):
        """Test getting threat assessment by asteroid ID when not found."""
        # Arrange
        service = ThreatService(mock_session_factory)

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo.get_by_asteroid_id = AsyncMock(return_value=None)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(999)

            # Assert
            assert result is None
            mock_uow.threat_repo.get_by_asteroid_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_get_high_risk(self, mock_session_factory):
        """Test getting high risk threat assessments."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ts_max": 6})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_high_risk_threats = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_high_risk(limit=20)

            # Assert
            assert len(result) == 1
            mock_uow.threat_repo.get_high_risk_threats.assert_called_once_with(limit=20, skip=0)

    @pytest.mark.asyncio
    async def test_get_high_risk_default_limit(self, mock_session_factory):
        """Test getting high risk threats with default limit."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ts_max": 6})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_high_risk_threats = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_high_risk()

            # Assert
            assert len(result) == 1
            mock_uow.threat_repo.get_high_risk_threats.assert_called_once_with(limit=20, skip=0)

    @pytest.mark.asyncio
    async def test_get_by_risk_level_with_defaults(self, mock_session_factory):
        """Test getting threat assessments by risk level with default pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ts_max": 3})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_risk_level = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_risk_level(min_ts=0, max_ts=10)

            # Assert
            assert len(result) == 1
            # Verify pagination parameters are passed with defaults
            mock_uow.threat_repo.get_threats_by_risk_level.assert_called_once_with(
                0, 10, skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_risk_level_with_custom_pagination(self, mock_session_factory):
        """Test getting threat assessments by risk level with custom pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ts_max": 3})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_risk_level = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_risk_level(min_ts=4, max_ts=6, skip=10, limit=50)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.threat_repo.get_threats_by_risk_level.assert_called_once_with(
                4, 6, skip=10, limit=50
            )

    @pytest.mark.asyncio
    async def test_get_by_probability_with_defaults(self, mock_session_factory):
        """Test getting threat assessments by probability with default pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ip": 0.001})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_probability = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_probability(min_probability=0.0, max_probability=1.0)

            # Assert
            assert len(result) == 1
            # Verify pagination parameters are passed with defaults
            mock_uow.threat_repo.get_threats_by_probability.assert_called_once_with(
                0.0, 1.0, skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_probability_with_custom_pagination(self, mock_session_factory):
        """Test getting threat assessments by probability with custom pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ip": 0.001})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_probability = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_probability(
                min_probability=0.001, max_probability=0.01, skip=5, limit=25
            )

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.threat_repo.get_threats_by_probability.assert_called_once_with(
                0.001, 0.01, skip=5, limit=25
            )

    @pytest.mark.asyncio
    async def test_get_by_energy_with_defaults(self, mock_session_factory):
        """Test getting threat assessments by energy with default pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"energy_megatons": 10.0})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_energy = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_energy(min_energy=0.0, max_energy=None)

            # Assert
            assert len(result) == 1
            # Verify pagination parameters are passed with defaults
            mock_uow.threat_repo.get_threats_by_energy.assert_called_once_with(
                0.0, None, skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_energy_with_custom_pagination(self, mock_session_factory):
        """Test getting threat assessments by energy with custom pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"energy_megatons": 50.0})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_energy = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_energy(
                min_energy=10.0, max_energy=100.0, skip=10, limit=50
            )

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.threat_repo.get_threats_by_energy.assert_called_once_with(
                10.0, 100.0, skip=10, limit=50
            )

    @pytest.mark.asyncio
    async def test_get_by_category_with_defaults(self, mock_session_factory):
        """Test getting threat assessments by category with default pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"impact_category": "локальный"})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_impact_category = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_category("локальный")

            # Assert
            assert len(result) == 1
            assert result[0]["impact_category"] == "локальный"
            # Verify pagination parameters are passed with defaults
            mock_uow.threat_repo.get_threats_by_impact_category.assert_called_once_with(
                "локальный", skip=0, limit=100
            )

    @pytest.mark.asyncio
    async def test_get_by_category_with_custom_pagination(self, mock_session_factory):
        """Test getting threat assessments by category with custom pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"impact_category": "региональный"})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_threats_by_impact_category = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_category("региональный", skip=5, limit=25)

            # Assert
            assert len(result) == 1
            # Verify custom pagination parameters are passed
            mock_uow.threat_repo.get_threats_by_impact_category.assert_called_once_with(
                "региональный", skip=5, limit=25
            )

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_session_factory):
        """Test getting threat assessment statistics."""
        # Arrange
        service = ThreatService(mock_session_factory)

        expected_stats = {
            "total_threats": 100,
            "torino_scale_distribution": {"ts_0": {"count": 50, "percent": 50.0}},
            "impact_category_distribution": {"локальный": {"count": 80, "percent": 80.0}},
            "average_probability": 0.001,
            "average_energy_mt": 10.0,
            "max_energy_mt": 100.0,
            "non_zero_probability_count": 5,
            "high_risk_count": 2,
            "last_updated": "2023-01-01T00:00:00"
        }

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo.get_statistics = AsyncMock(return_value=expected_stats)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_statistics()

            # Assert
            assert result == expected_stats
            mock_uow.threat_repo.get_statistics.assert_called_once()

    def test_model_to_dict_with_none(self):
        """Test converting None model to dictionary."""
        # Arrange
        service = ThreatService(Mock())

        # Act
        result = service._model_to_dict(None)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_all_methods_use_uow_correctly(self, mock_session_factory):
        """Test that all service methods properly use UnitOfWork with pagination."""
        # Arrange
        service = ThreatService(mock_session_factory)
        service._model_to_dict = Mock(return_value={"ts_max": 1})

        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        
        mock_threat = Mock()
        mock_uow.threat_repo.get_by_designation = AsyncMock(return_value=mock_threat)
        mock_uow.threat_repo.get_by_asteroid_id = AsyncMock(return_value=mock_threat)
        mock_uow.threat_repo.get_high_risk_threats = AsyncMock(return_value=[mock_threat])
        mock_uow.threat_repo.get_threats_by_risk_level = AsyncMock(return_value=[mock_threat])
        mock_uow.threat_repo.get_statistics = AsyncMock(return_value={})
        mock_uow.threat_repo.get_threats_by_energy = AsyncMock(return_value=[mock_threat])
        mock_uow.threat_repo.get_threats_by_impact_category = AsyncMock(return_value=[mock_threat])
        mock_uow.threat_repo.get_threats_by_probability = AsyncMock(return_value=[mock_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act - Call all methods
            await service.get_by_designation("2023 TEST")
            await service.get_by_asteroid_id(1)
            await service.get_high_risk(limit=20)
            await service.get_by_risk_level(min_ts=0, max_ts=10, skip=0, limit=100)
            await service.get_statistics()
            await service.get_by_energy(min_energy=0.0, max_energy=100.0, skip=0, limit=100)
            await service.get_by_category("локальный", skip=0, limit=100)
            await service.get_by_probability(min_probability=0.0, max_probability=1.0, skip=0, limit=100)

            # Assert - All methods should have used UoW with correct pagination
            mock_uow.threat_repo.get_by_designation.assert_called_once_with("2023 TEST")
            mock_uow.threat_repo.get_by_asteroid_id.assert_called_once_with(1)
            mock_uow.threat_repo.get_high_risk_threats.assert_called_once_with(limit=20, skip=0)
            mock_uow.threat_repo.get_threats_by_risk_level.assert_called_once_with(
                0, 10, skip=0, limit=100
            )
            mock_uow.threat_repo.get_statistics.assert_called_once()
            mock_uow.threat_repo.get_threats_by_energy.assert_called_once_with(
                0.0, 100.0, skip=0, limit=100
            )
            mock_uow.threat_repo.get_threats_by_impact_category.assert_called_once_with(
                "локальный", skip=0, limit=100
            )
            mock_uow.threat_repo.get_threats_by_probability.assert_called_once_with(
                0.0, 1.0, skip=0, limit=100
            )
