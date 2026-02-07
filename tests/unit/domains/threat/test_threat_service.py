import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from domains.threat.services.threat_service import ThreatService


class TestThreatService:
    """Unit tests for ThreatService class."""

    def test_threat_service_initialization(self):
        """Test initializing the threat service."""
        # Arrange
        mock_session_factory = Mock()
        
        # Act
        service = ThreatService(mock_session_factory)
        
        # Assert
        assert service.session_factory == mock_session_factory

    @pytest.mark.asyncio
    async def test_get_by_designation_found(self, mock_session_factory, sample_threat_data):
        """Test getting threat assessment by designation when found."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        # Extend sample_threat_data with designation which is expected by the test
        extended_threat_data = {**sample_threat_data, "designation": "2023 DW"}
        
        # Create a simple object with the expected attributes instead of a complex mock
        from types import SimpleNamespace
        expected_threat = SimpleNamespace(**extended_threat_data)
        # Add the table structure for the _model_to_dict method
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key in extended_threat_data.keys():
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_by_designation = AsyncMock(return_value=expected_threat)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("2023 DW")

            # Assert
            assert result is not None
            assert result["designation"] == "2023 DW"
            mock_uow.threat_repo.get_by_designation.assert_called_once_with("2023 DW")

    @pytest.mark.asyncio
    async def test_get_by_designation_not_found(self, mock_session_factory):
        """Test getting threat assessment by designation when not found."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session
        mock_uow.threat_repo.get_by_designation = AsyncMock(return_value=None)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_designation("nonexistent")

            # Assert
            assert result is None
            mock_uow.threat_repo.get_by_designation.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_found(self, mock_session_factory, sample_threat_data):
        """Test getting threat assessment by asteroid ID when found."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        expected_threat = Mock()
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key, value in sample_threat_data.items():
            setattr(expected_threat, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_by_asteroid_id = AsyncMock(return_value=expected_threat)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(1)

            # Assert
            assert result is not None
            assert result["asteroid_id"] == sample_threat_data["asteroid_id"]
            mock_uow.threat_repo.get_by_asteroid_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id_not_found(self, mock_session_factory):
        """Test getting threat assessment by asteroid ID when not found."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session
        mock_uow.threat_repo.get_by_asteroid_id = AsyncMock(return_value=None)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_asteroid_id(999)

            # Assert
            assert result is None
            mock_uow.threat_repo.get_by_asteroid_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_get_high_risk(self, mock_session_factory, sample_threat_data):
        """Test getting high risk threat assessments."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        expected_threat = Mock()
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key, value in sample_threat_data.items():
            setattr(expected_threat, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_high_risk_threats = AsyncMock(return_value=[expected_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_high_risk(limit=20)

            # Assert
            assert len(result) == 1
            assert result[0]["torino_scale"] == sample_threat_data["torino_scale"]
            mock_uow.threat_repo.get_high_risk_threats.assert_called_once_with(20)

    @pytest.mark.asyncio
    async def test_get_by_risk_level(self, mock_session_factory, sample_threat_data):
        """Test getting threat assessments by risk level."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        expected_threat = Mock()
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key, value in sample_threat_data.items():
            setattr(expected_threat, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_threats_by_risk_level = AsyncMock(return_value=[expected_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_risk_level(min_ts=4, max_ts=6)

            # Assert
            assert len(result) == 1
            mock_uow.threat_repo.get_threats_by_risk_level.assert_called_once_with(4, 6)

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_session_factory):
        """Test getting threat assessment statistics."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

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

        mock_uow.threat_repo.get_statistics = AsyncMock(return_value=expected_stats)

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_statistics()

            # Assert
            assert result == expected_stats
            mock_uow.threat_repo.get_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_energy(self, mock_session_factory, sample_threat_data):
        """Test getting threat assessments by energy range."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        expected_threat = Mock()
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key, value in sample_threat_data.items():
            setattr(expected_threat, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_threats_by_energy = AsyncMock(return_value=[expected_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_energy(min_energy=10.0, max_energy=100.0)

            # Assert
            assert len(result) == 1
            mock_uow.threat_repo.get_threats_by_energy.assert_called_once_with(10.0, 100.0)

    @pytest.mark.asyncio
    async def test_get_by_energy_no_max(self, mock_session_factory, sample_threat_data):
        """Test getting threat assessments by minimum energy only."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        expected_threat = Mock()
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key, value in sample_threat_data.items():
            setattr(expected_threat, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_threats_by_energy = AsyncMock(return_value=[expected_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_energy(min_energy=10.0)

            # Assert
            assert len(result) == 1
            mock_uow.threat_repo.get_threats_by_energy.assert_called_once_with(10.0, None)

    @pytest.mark.asyncio
    async def test_get_by_category(self, mock_session_factory, sample_threat_data):
        """Test getting threat assessments by category."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session

        expected_threat = Mock()
        expected_threat.__table__ = Mock()
        expected_threat.__table__.columns = []
        for key, value in sample_threat_data.items():
            setattr(expected_threat, key, value)
            mock_col = Mock()
            mock_col.name = key
            expected_threat.__table__.columns.append(mock_col)

        mock_uow.threat_repo.get_threats_by_impact_category = AsyncMock(return_value=[expected_threat])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act
            result = await service.get_by_category("региональный")

            # Assert
            assert len(result) == 1
            mock_uow.threat_repo.get_threats_by_impact_category.assert_called_once_with("региональный")

    def test_model_to_dict_with_valid_model(self, sample_threat_data):
        """Test converting model instance to dictionary."""
        # Arrange
        service = ThreatService(Mock())
        
        mock_model = Mock()
        mock_model.__table__ = Mock()
        mock_model.__table__.columns = []
        
        for key, value in sample_threat_data.items():
            setattr(mock_model, key, value)
            mock_col = Mock()
            mock_col.name = key
            mock_model.__table__.columns.append(mock_col)
        
        # Act
        result = service._model_to_dict(mock_model)
        
        # Assert
        assert result is not None
        for key, expected_value in sample_threat_data.items():
            assert result[key] == expected_value

    def test_model_to_dict_with_none(self):
        """Test converting None model to dictionary."""
        # Arrange
        service = ThreatService(Mock())
        
        # Act
        result = service._model_to_dict(None)
        
        # Assert
        assert result is None

    def test_model_to_dict_with_relationships(self, sample_threat_data):
        """Test converting model instance with relationships to dictionary."""
        # Arrange
        service = ThreatService(Mock())

        # Use SimpleNamespace to avoid _mock_methods conflicts
        from types import SimpleNamespace

        mock_model = SimpleNamespace()
        mock_model.__dict__.update(sample_threat_data)

        # Create a mock table
        mock_table = Mock()
        mock_table.columns = []
        for key in sample_threat_data.keys():
            mock_col = Mock()
            mock_col.name = key
            mock_table.columns.append(mock_col)
        mock_model.__table__ = mock_table

        # Add a relationship attribute
        mock_related_model = SimpleNamespace(id=1, name="Related")
        mock_related_table = Mock()
        mock_related_table.columns = []
        for attr in ["id", "name"]:
            mock_col = Mock()
            mock_col.name = attr
            mock_related_table.columns.append(mock_col)
        mock_related_model.__table__ = mock_related_table

        mock_model.related_field = mock_related_model

        # Act
        result = service._model_to_dict(mock_model)

        # Assert
        assert result is not None
        for key, expected_value in sample_threat_data.items():
            assert result[key] == expected_value
        assert "related_field" in result

    @pytest.mark.asyncio
    async def test_service_methods_use_uow_properly(self, mock_session_factory):
        """Test that all service methods properly use UnitOfWork."""
        # Arrange
        service = ThreatService(mock_session_factory)

        # Mock the UoW context manager
        mock_uow = Mock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.threat_repo = Mock()
        mock_session = Mock()
        mock_uow.threat_repo.session = mock_session
        
        mock_uow.threat_repo.get_by_designation = AsyncMock(return_value=None)
        mock_uow.threat_repo.get_by_asteroid_id = AsyncMock(return_value=None)
        mock_uow.threat_repo.get_high_risk_threats = AsyncMock(return_value=[])
        mock_uow.threat_repo.get_threats_by_risk_level = AsyncMock(return_value=[])
        mock_uow.threat_repo.get_statistics = AsyncMock(return_value={})
        mock_uow.threat_repo.get_threats_by_energy = AsyncMock(return_value=[])
        mock_uow.threat_repo.get_threats_by_impact_category = AsyncMock(return_value=[])

        with patch('shared.transaction.uow.UnitOfWork', return_value=mock_uow):
            # Act - Call all the methods
            await service.get_by_designation("2023 DW")
            await service.get_by_asteroid_id(1)
            await service.get_high_risk(limit=20)
            await service.get_by_risk_level(min_ts=0, max_ts=10)
            await service.get_statistics()
            await service.get_by_energy(min_energy=0.0, max_energy=100.0)
            await service.get_by_category("локальный")

            # Assert - All methods should have used UoW
            mock_uow.threat_repo.get_by_designation.assert_called_once_with("2023 DW")
            mock_uow.threat_repo.get_by_asteroid_id.assert_called_once_with(1)
            mock_uow.threat_repo.get_high_risk_threats.assert_called_once_with(20)
            mock_uow.threat_repo.get_threats_by_risk_level.assert_called_once_with(0, 10)
            mock_uow.threat_repo.get_statistics.assert_called_once()
            mock_uow.threat_repo.get_threats_by_energy.assert_called_once_with(0.0, 100.0)
            mock_uow.threat_repo.get_threats_by_impact_category.assert_called_once_with("локальный")