import pytest
from datetime import datetime
from domains.threat.models.threat_assessment import ThreatAssessmentModel


class TestThreatAssessmentModel:
    """Unit tests for ThreatAssessmentModel class."""

    def test_threat_assessment_model_creation_with_valid_data(self):
        """Test creating a threat assessment model with valid data."""
        assessment = ThreatAssessmentModel(
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
            impact_years=[2025, 2030, 2035],
            last_obs="2023-01-01",
            threat_level_ru="НИЗКИЙ (требует наблюдения)",
            torino_scale_ru="Низкий риск",
            impact_probability_text_ru="Низкая вероятность столкновения",
            energy_megatons=10.0,
            impact_category="локальный",
            sentry_last_update=datetime.now()
        )

        assert assessment.asteroid_id == 1
        assert assessment.designation == "2023 DW"
        assert assessment.fullname == "2023 DW (Asteroid)"
        assert assessment.ip == 0.001
        assert assessment.ts_max == 1
        assert assessment.ps_max == 0.5
        assert assessment.diameter == 0.1
        assert assessment.v_inf == 10.5
        assert assessment.h == 20.5
        assert assessment.n_imp == 5
        assert assessment.impact_years == [2025, 2030, 2035]
        assert assessment.last_obs == "2023-01-01"
        assert assessment.threat_level_ru == "НИЗКИЙ (требует наблюдения)"
        assert assessment.torino_scale_ru == "Низкий риск"
        assert assessment.impact_probability_text_ru == "Низкая вероятность столкновения"
        assert assessment.energy_megatons == 10.0
        assert assessment.impact_category == "локальный"

    def test_threat_assessment_model_creation_with_defaults(self):
        """Test creating a threat assessment model with minimal required data."""
        update_time = datetime.now()
        assessment = ThreatAssessmentModel(
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
            sentry_last_update=update_time
        )

        assert assessment.asteroid_id == 1
        assert assessment.designation == "2023 DW"
        assert assessment.fullname == "2023 DW (Asteroid)"
        assert assessment.ip == 0.001
        assert assessment.ts_max == 1
        assert assessment.ps_max == 0.5
        assert assessment.diameter == 0.1
        assert assessment.v_inf == 10.5
        assert assessment.h == 20.5
        assert assessment.n_imp == 5
        assert assessment.impact_years == [2025]
        assert assessment.last_obs == "2023-01-01"
        assert assessment.sentry_last_update == update_time
        # Fields with defaults should be set
        assert assessment.energy_megatons > 0  # Calculated from diameter and velocity
        assert assessment.impact_category in ['локальный', 'региональный', 'глобальный']
        assert assessment.threat_level_ru is not None

    def test_threat_assessment_model_energy_calculation(self):
        """Test that energy is automatically calculated from diameter and velocity."""
        update_time = datetime.now()
        assessment = ThreatAssessmentModel(
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter=0.1,  # 100m diameter
            v_inf=20.0,    # 20 km/s velocity
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            sentry_last_update=update_time
        )

        # Energy should be calculated based on diameter and velocity
        assert assessment.energy_megatons > 0

    def test_threat_assessment_model_energy_override(self):
        """Test that provided energy is preserved."""
        update_time = datetime.now()
        provided_energy = 50.0
        assessment = ThreatAssessmentModel(
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
            energy_megatons=provided_energy,  # Provide specific energy
            sentry_last_update=update_time
        )

        # Should use the provided energy, not calculate
        assert assessment.energy_megatons == provided_energy

    def test_threat_assessment_model_impact_category_determination(self):
        """Test that impact category is determined based on energy."""
        update_time = datetime.now()
        # Low energy assessment
        low_energy_assessment = ThreatAssessmentModel(
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter=0.01,  # Small diameter -> low energy
            v_inf=10.5,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            sentry_last_update=update_time
        )

        assert low_energy_assessment.impact_category == 'локальный'

        # High energy assessment
        high_energy_assessment = ThreatAssessmentModel(
            asteroid_id=2,
            designation="2023 DW2",
            fullname="2023 DW2 (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter=10.0,  # Large diameter -> high energy
            v_inf=20.0,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            sentry_last_update=update_time
        )

        # The energy should be high enough for regional/global category
        assert high_energy_assessment.impact_category in ['региональный', 'глобальный']

    def test_threat_assessment_model_threat_level_assessment(self):
        """Test that threat level is assessed based on Torino and Palermo scales."""
        update_time = datetime.now()
        # Low threat assessment
        low_threat_assessment = ThreatAssessmentModel(
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.0001,  # Very low probability
            ts_max=0,    # Zero on Torino scale
            ps_max=-5.0, # Low on Palermo scale
            diameter=0.1,
            v_inf=10.5,
            h=20.5,
            n_imp=1,
            impact_years=[2025],
            last_obs="2023-01-01",
            sentry_last_update=update_time
        )

        # Should be a low/no threat level
        assert "НИЗКИЙ" in low_threat_assessment.threat_level_ru or "НУЛЕВОЙ" in low_threat_assessment.threat_level_ru

        # Higher threat assessment
        higher_threat_assessment = ThreatAssessmentModel(
            asteroid_id=2,
            designation="2023 DW2",
            fullname="2023 DW2 (Asteroid)",
            ip=0.01,  # Higher probability
            ts_max=5,  # Moderate on Torino scale
            ps_max=1.0,  # Positive on Palermo scale
            diameter=0.1,
            v_inf=10.5,
            h=20.5,
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            sentry_last_update=update_time
        )

        # Should be a medium threat level
        assert "СРЕДНИЙ" in higher_threat_assessment.threat_level_ru

    def test_threat_assessment_model_field_mapping(self):
        """Test that field mappings work correctly."""
        update_time = datetime.now()
        # Test with alternative field names that should be mapped
        assessment = ThreatAssessmentModel(
            asteroid_id=1,
            designation="2023 DW",
            fullname="2023 DW (Asteroid)",
            ip=0.001,
            ts_max=1,
            ps_max=0.5,
            diameter_km=0.1,  # Should map to 'diameter'
            velocity_km_s=10.5,  # Should map to 'v_inf'
            absolute_magnitude=20.5,  # Should map to 'h'
            n_imp=5,
            impact_years=[2025],
            last_obs="2023-01-01",
            sentry_last_update=update_time
        )

        assert assessment.diameter == 0.1
        assert assessment.v_inf == 10.5
        assert assessment.h == 20.5

    def test_threat_assessment_model_repr(self):
        """Test string representation of threat assessment model."""
        update_time = datetime.now()
        assessment = ThreatAssessmentModel(
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
            sentry_last_update=update_time
        )

        expected_repr = f"ThreatAssessmentModel(id=1, asteroid_id=1, threat=НИЗКИЙ (требует наблюдения))"
        assert repr(assessment) == expected_repr