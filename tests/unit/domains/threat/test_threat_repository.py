import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from domains.threat.models.threat_assessment import ThreatAssessmentModel
from domains.threat.repositories.threat_repository import ThreatRepository


class TestThreatRepository:
    """Unit tests for ThreatRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_designation(self, mock_session):
        """Test getting threat assessment by designation."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threat = ThreatAssessmentModel(
            id=1,
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter=0.1,
            v_inf=10.5,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            threat_level_ru="НИЗКИЙ (требует наблюдения)",
            torino_scale_ru="Низкий риск",
            impact_probability_text_ru="Низкая вероятность столкновения",
            energy_megatons=10.0,
            impact_category="локальный",
            sentry_last_update=datetime.now()
        )

        # Mock the _find_by_fields method to return the threat
        repo._find_by_fields = AsyncMock(return_value=expected_threat)
        
        # Act
        result = await repo.get_by_designation("2023 DW")

        # Assert
        assert result == expected_threat
        repo._find_by_fields.assert_called_once_with({"designation": "2023 DW"})

    @pytest.mark.asyncio
    async def test_get_by_asteroid_id(self, mock_session):
        """Test getting threat assessment by asteroid ID."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threat = ThreatAssessmentModel(
            id=1,
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter=0.1,
            v_inf=10.5,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            threat_level_ru="НИЗКИЙ (требует наблюдения)",
            torino_scale_ru="Низкий риск",
            impact_probability_text_ru="Низкая вероятность столкновения",
            energy_megatons=10.0,
            impact_category="локальный",
            sentry_last_update=datetime.now()
        )

        # Mock the _find_by_fields method to return the threat
        repo._find_by_fields = AsyncMock(return_value=expected_threat)
        
        # Act
        result = await repo.get_by_asteroid_id(1)

        # Assert
        assert result == expected_threat
        repo._find_by_fields.assert_called_once_with({"asteroid_id": 1})

    @pytest.mark.asyncio
    async def test_get_high_risk_threats(self, mock_session):
        """Test getting high risk threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.01,
                ts_max=6,  # High risk
                ps_max=1.0,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="ПОВЫШЕННЫЙ (серьёзная угроза)",
                torino_scale_ru="Повышенная угроза",
                impact_probability_text_ru="Повышенная вероятность столкновения",
                energy_megatons=10.0,
                impact_category="локальный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the filter method to return the threats
        repo.filter = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.get_high_risk_threats(limit=20)

        # Assert
        assert result == expected_threats
        repo.filter.assert_called_once_with(
            filters={"ts_max__ge": 5},
            limit=20,
            order_by="ts_max",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_get_threats_by_risk_level(self, mock_session):
        """Test getting threats by risk level (Torino scale)."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.001,
                ts_max=5,  # Medium risk
                ps_max=0.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="СРЕДНИЙ (заслуживает внимания астрономов)",
                torino_scale_ru="Средний риск",
                impact_probability_text_ru="Средняя вероятность столкновения",
                energy_megatons=10.0,
                impact_category="локальный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the filter method to return the threats
        repo.filter = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.get_threats_by_risk_level(min_ts=4, max_ts=6)

        # Assert
        assert result == expected_threats
        repo.filter.assert_called_once_with(
            filters={"ts_max__ge": 4, "ts_max__le": 6},
            skip=0,
            limit=100,
            order_by="ts_max",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_get_threats_by_probability(self, mock_session):
        """Test getting threats by probability range."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.005,
                ts_max=1,
                ps_max=0.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ (требует наблюдения)",
                torino_scale_ru="Низкий риск",
                impact_probability_text_ru="Низкая вероятность столкновения",
                energy_megatons=10.0,
                impact_category="локальный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the filter method to return the threats
        repo.filter = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.get_threats_by_probability(
            min_probability=0.001, max_probability=0.01
        )

        # Assert
        assert result == expected_threats
        repo.filter.assert_called_once_with(
            filters={"ip__ge": 0.001, "ip__le": 0.01},
            skip=0,
            limit=100,
            order_by="ip",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_get_threats_by_energy(self, mock_session):
        """Test getting threats by energy range."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.001,
                ts_max=1,
                ps_max=0.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ (требует наблюдения)",
                torino_scale_ru="Низкий риск",
                impact_probability_text_ru="Низкая вероятность столкновения",
                energy_megatons=50.0,  # High energy
                impact_category="локальный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the filter method to return the threats
        repo.filter = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.get_threats_by_energy(
            min_energy=10.0, max_energy=100.0
        )

        # Assert
        assert result == expected_threats
        repo.filter.assert_called_once_with(
            filters={"energy_megatons__ge": 10.0, "energy_megatons__le": 100.0},
            skip=0,
            limit=100,
            order_by="energy_megatons",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_get_threats_by_energy_no_max(self, mock_session):
        """Test getting threats by minimum energy only."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.001,
                ts_max=1,
                ps_max=0.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ (требует наблюдения)",
                torino_scale_ru="Низкий риск",
                impact_probability_text_ru="Низкая вероятность столкновения",
                energy_megatons=50.0,
                impact_category="локальный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the filter method to return the threats
        repo.filter = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.get_threats_by_energy(min_energy=10.0)

        # Assert
        assert result == expected_threats
        repo.filter.assert_called_once_with(
            filters={"energy_megatons__ge": 10.0},
            skip=0,
            limit=100,
            order_by="energy_megatons",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_get_threats_by_impact_category(self, mock_session):
        """Test getting threats by impact category."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.001,
                ts_max=1,
                ps_max=0.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ (требует наблюдения)",
                torino_scale_ru="Низкий риск",
                impact_probability_text_ru="Низкая вероятность столкновения",
                energy_megatons=50.0,
                impact_category="региональный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the filter method to return the threats
        repo.filter = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.get_threats_by_impact_category("региональный")

        # Assert
        assert result == expected_threats
        repo.filter.assert_called_once_with(
            filters={"impact_category": "региональный"},
            skip=0,
            limit=100,
            order_by="energy_megatons",
            order_desc=True
        )

    @pytest.mark.asyncio
    async def test_update_threat_assessment(self, mock_session):
        """Test updating threat assessment."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        existing_threat = ThreatAssessmentModel(
            id=1,
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter=0.1,
            v_inf=10.5,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            threat_level_ru="НИЗКИЙ (требует наблюдения)",
            torino_scale_ru="Низкий риск",
            impact_probability_text_ru="Низкая вероятность столкновения",
            energy_megatons=10.0,
            impact_category="локальный",
            sentry_last_update=datetime.now()
        )

        updated_data = {
            "ip": 0.002,
            "ts_max": 2,
            "energy_megatons": 15.0
        }

        updated_threat = ThreatAssessmentModel(
            id=1,
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.002,
            ts_max=2,
            ps_max=0.5,
            diameter=0.1,
            v_inf=10.5,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            threat_level_ru="НИЗКИЙ (требует наблюдения)",
            torino_scale_ru="Низкий риск",
            impact_probability_text_ru="Низкая вероятность столкновения",
            energy_megatons=15.0,
            impact_category="локальный",
            sentry_last_update=datetime.now()
        )

        # Mock the get_by_designation method to return the existing threat
        repo.get_by_designation = AsyncMock(return_value=existing_threat)
        # Mock the update method to return the updated threat
        repo.update = AsyncMock(return_value=updated_threat)

        # Act
        result = await repo.update_threat_assessment("2023 DW", updated_data)

        # Assert
        assert result == updated_threat
        repo.get_by_designation.assert_called_once_with("2023 DW")
        repo.update.assert_called_once_with(1, updated_data)

    @pytest.mark.asyncio
    async def test_update_threat_assessment_not_found(self, mock_session):
        """Test updating threat assessment when not found."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session

        # Mock the get_by_designation method to return None
        repo.get_by_designation = AsyncMock(return_value=None)

        # Act
        result = await repo.update_threat_assessment("nonexistent", {})

        # Assert
        assert result is None
        repo.get_by_designation.assert_called_once_with("nonexistent")

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
                "ps_max": 0.5,
                "diameter": 0.1,
                "v_inf": 10.5,
                "h": 20.5,
                "n_imp": 5,
                "impact_years": [2025],
                "last_obs": "2023-01-01",
                "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
                "torino_scale_ru": "Низкий риск",
                "impact_probability_text_ru": "Низкая вероятность столкновения",
                "energy_megatons": 10.0,
                "impact_category": "локальный",
                "sentry_last_update": datetime.now()
            }
        ]

        # Mock the bulk_create method
        repo.bulk_create = AsyncMock(return_value=(3, 1))  # 3 created, 1 updated

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
    async def test_get_statistics_success(self, mock_session):
        """Test getting statistics for threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session

        # Mock the count method
        repo.count = AsyncMock(return_value=100)

        # Mock the SQLAlchemy queries
        mock_execute = AsyncMock()
        mock_result = Mock()
        mock_result.scalar = Mock()

        # Track the number of calls to simulate the sequence of scalar calls in the method
        scalar_calls = []
        def mock_scalar_side_effect():
            # There are multiple queries in the method:
            # 1. 11 torino scale queries (ts_0 to ts_10)
            # 2. 3 category queries (локальный, региональный, глобальный)
            # 3. average probability
            # 4. max energy
            # 5. average energy
            # 6. non-zero probability count
            # 7. high-risk count
            # Total 11 + 3 + 1 + 1 + 1 + 1 + 1 = 19 calls

            call_index = len(scalar_calls)
            scalar_calls.append(1)  # Track the call

            if call_index < 11:  # torino scale queries (0-10)
                return 5  # Count for each scale
            elif call_index < 14:  # category queries (локальный, региональный, глобальный)
                return 10  # Count for each category
            elif call_index == 14:  # average probability
                return 0.001
            elif call_index == 15:  # max energy
                return 100.0
            elif call_index == 16:  # average energy
                return 50.0
            elif call_index == 17:  # non-zero probability count
                return 20
            elif call_index == 18:  # high-risk count
                return 5
            else:
                return 0  # Default for any extra calls

        mock_result.scalar.side_effect = mock_scalar_side_effect
        mock_execute.return_value = mock_result
        mock_session.execute = mock_execute

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
    async def test_get_statistics_empty_database(self, mock_session):
        """Test getting statistics when database is empty."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session

        # Mock the count method to return 0
        repo.count = AsyncMock(return_value=0)

        # Mock the SQLAlchemy queries to return None or 0
        mock_execute = AsyncMock()
        mock_result = Mock()
        mock_result.scalar = Mock()

        # Track the number of calls to simulate the sequence of scalar calls in the method
        scalar_calls = []
        def mock_scalar_side_effect():
            # Same sequence as above, but all return 0 since DB is empty
            call_index = len(scalar_calls)
            scalar_calls.append(1)  # Track the call

            if call_index < 11:  # torino scale queries (0-10)
                return 0  # Count for each scale
            elif call_index < 14:  # category queries (локальный, региональный, глобальный)
                return 0  # Count for each category
            elif call_index == 14:  # average probability
                return 0
            elif call_index == 15:  # max energy
                return 0
            elif call_index == 16:  # average energy
                return 0
            elif call_index == 17:  # non-zero probability count
                return 0
            elif call_index == 18:  # high-risk count
                return 0
            else:
                return 0  # Default for any extra calls

        mock_result.scalar.side_effect = mock_scalar_side_effect
        mock_execute.return_value = mock_result
        mock_session.execute = mock_execute

        # Act
        result = await repo.get_statistics()

        # Assert
        assert result["total_threats"] == 0
        # Check that percentages are 0 when total is 0
        assert result["torino_scale_distribution"]["ts_0"]["percent"] == 0
        assert result["impact_category_distribution"]["локальный"]["percent"] == 0

    @pytest.mark.asyncio
    async def test_search_threats(self, mock_session):
        """Test searching threats."""
        # Arrange
        repo = ThreatRepository()
        repo.session = mock_session
        expected_threats = [
            ThreatAssessmentModel(
                id=1,
                asteroid_id=1,
                designation="2023 DW",
                fullname="2023 DW (Asteroid)",
                ip=0.001,
                ts_max=1,
                ps_max=0.5,
                diameter=0.1,
                v_inf=10.5,
                h=20.5,
                n_imp=5,
                impact_years=[2025],
                last_obs="2023-01-01",
                threat_level_ru="НИЗКИЙ (требует наблюдения)",
                torino_scale_ru="Низкий риск",
                impact_probability_text_ru="Низкая вероятность столкновения",
                energy_megatons=10.0,
                impact_category="локальный",
                sentry_last_update=datetime.now()
            )
        ]

        # Mock the search method to return the threats
        repo.search = AsyncMock(return_value=expected_threats)
        
        # Act
        result = await repo.search_threats("2023 DW")

        # Assert
        assert result == expected_threats
        repo.search.assert_called_once_with(
            search_term="2023 DW",
            search_fields=["designation", "fullname"],
            skip=0,
            limit=50
        )

    @pytest.mark.asyncio
    async def test_get_statistics_exception_handling(self, mock_session):
        """Test that exceptions in get_statistics are properly handled."""
        # Arrange
        repo = ThreatRepository()
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