import pytest
from pydantic import ValidationError
from datetime import datetime
from domains.threat.schemas.threat_schema import ThreatAssessmentBase, ThreatAssessmentCreate, ThreatAssessmentResponse


class TestThreatAssessmentCreateSchema:
    """Unit tests for ThreatAssessmentCreate schema."""

    def test_threat_assessment_create_schema_valid_data(self):
        """Test creating threat assessment with valid data passes validation."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025, 2030, 2035],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        assessment = ThreatAssessmentCreate(**data)

        assert assessment.asteroid_id == 1
        assert assessment.designation == "2023 DW"
        assert assessment.fullname == "2023 DW (Asteroid)"
        assert assessment.ip == 0.001
        assert assessment.ts_max == 1
        assert assessment.ps_max == 0.5
        assert assessment.diameter_km == 0.1
        assert assessment.velocity_km_s == 10.5
        assert assessment.absolute_magnitude == 20.5
        assert assessment.n_imp == 5
        assert assessment.impact_years == [2025, 2030, 2035]
        assert assessment.last_obs == "2023-01-01"
        assert assessment.threat_level_ru == "НИЗКИЙ (требует наблюдения)"
        assert assessment.torino_scale_ru == "Низкий риск"
        assert assessment.impact_probability_text_ru == "Низкая вероятность столкновения"
        assert assessment.energy_megatons == 0.0  # Default value
        assert assessment.impact_category == "локальный"  # Default value

    def test_threat_assessment_create_schema_with_optional_fields(self):
        """Test creating threat assessment with optional fields."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025, 2030, 2035],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения",
            "energy_megatons": 10.0,
            "impact_category": "региональный"
        }

        assessment = ThreatAssessmentCreate(**data)

        assert assessment.asteroid_id == 1
        assert assessment.designation == "2023 DW"
        assert assessment.fullname == "2023 DW (Asteroid)"
        assert assessment.ip == 0.001
        assert assessment.ts_max == 1
        assert assessment.ps_max == 0.5
        assert assessment.diameter_km == 0.1
        assert assessment.velocity_km_s == 10.5
        assert assessment.absolute_magnitude == 20.5
        assert assessment.n_imp == 5
        assert assessment.impact_years == [2025, 2030, 2035]
        assert assessment.last_obs == "2023-01-01"
        assert assessment.threat_level_ru == "НИЗКИЙ (требует наблюдения)"
        assert assessment.torino_scale_ru == "Низкий риск"
        assert assessment.impact_probability_text_ru == "Низкая вероятность столкновения"
        assert assessment.energy_megatons == 10.0
        assert assessment.impact_category == "региональный"

    def test_threat_assessment_create_schema_ip_validation_valid_range(self):
        """Test that IP values in valid range pass validation."""
        valid_values = [0.0, 0.1, 0.5, 0.9, 1.0]

        for value in valid_values:
            data = {
                "asteroid_id": 1,
                "designation": "2023 DW",
                "fullname": "2023 DW (Asteroid)",
                "ip": value,
                "ts_max": 1,
                "ps_max": 0.5,
                "diameter_km": 0.1,
                "velocity_km_s": 10.5,
                "absolute_magnitude": 20.5,
                "n_imp": 5,
                "impact_years": [2025],
                "last_obs": "2023-01-01",
                "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
                "torino_scale_ru": "Низкий риск",
                "impact_probability_text_ru": "Низкая вероятность столкновения"
            }

            assessment = ThreatAssessmentCreate(**data)
            assert assessment.ip == value

    def test_threat_assessment_create_schema_ip_validation_below_range(self):
        """Test that IP values below range raise ValidationError."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": -0.1,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_ip_validation_above_range(self):
        """Test that IP values above range raise ValidationError."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 1.1,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_ts_max_validation_valid_range(self):
        """Test that TS_MAX values in valid range pass validation."""
        valid_values = [0, 1, 5, 9, 10]

        for value in valid_values:
            data = {
                "asteroid_id": 1,
                "designation": "2023 DW",
                "fullname": "2023 DW (Asteroid)",
                "ip": 0.001,
                "ts_max": value,
                "ps_max": 0.5,
                "diameter_km": 0.1,
                "velocity_km_s": 10.5,
                "absolute_magnitude": 20.5,
                "n_imp": 5,
                "impact_years": [2025],
                "last_obs": "2023-01-01",
                "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
                "torino_scale_ru": "Низкий риск",
                "impact_probability_text_ru": "Низкая вероятность столкновения"
            }

            assessment = ThreatAssessmentCreate(**data)
            assert assessment.ts_max == value

    def test_threat_assessment_create_schema_ts_max_validation_below_range(self):
        """Test that TS_MAX values below range raise ValidationError."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": -1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_ts_max_validation_above_range(self):
        """Test that TS_MAX values above range raise ValidationError."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 11,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_diameter_validation_non_negative(self):
        """Test that diameter values are non-negative."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": -0.1,  # Negative diameter
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_velocity_validation_non_negative(self):
        """Test that velocity values are non-negative."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": -1.0,  # Negative velocity
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_energy_validation_non_negative(self):
        """Test that energy values are non-negative."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения",
            "energy_megatons": -1.0  # Negative energy
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_n_imp_validation_non_negative(self):
        """Test that n_imp values are non-negative."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": -1,  # Negative n_imp
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_required_fields_missing(self):
        """Test that missing required fields raise ValidationError."""
        required_fields_tests = [
            {},  # No fields
            {"asteroid_id": 1},  # Missing all required fields except asteroid_id
            {"asteroid_id": 1, "designation": "2023 DW"},  # Missing fullname, ip, etc.
        ]

        for data in required_fields_tests:
            with pytest.raises(ValidationError):
                ThreatAssessmentCreate(**data)

    def test_threat_assessment_create_schema_impact_years_can_be_empty_list(self):
        """Test that impact years can be an empty list."""
        data = {
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 0,
            "impact_years": [],  # Empty list is valid
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения"
        }

        assessment = ThreatAssessmentCreate(**data)

        assert assessment.asteroid_id == 1
        assert assessment.impact_years == []


class TestThreatAssessmentBaseSchema:
    """Unit tests for ThreatAssessmentBase schema."""

    def test_threat_assessment_base_schema_valid_data(self):
        """Test creating threat assessment base with valid data."""
        created_at = datetime.now()
        updated_at = datetime.now()
        data = {
            "id": 1,
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025, 2030, 2035],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения",
            "energy_megatons": 10.0,
            "impact_category": "локальный",
            "created_at": created_at,
            "updated_at": updated_at
        }

        assessment = ThreatAssessmentBase(**data)

        assert assessment.id == 1
        assert assessment.asteroid_id == 1
        assert assessment.designation == "2023 DW"
        assert assessment.fullname == "2023 DW (Asteroid)"
        assert assessment.ip == 0.001
        assert assessment.ts_max == 1
        assert assessment.ps_max == 0.5
        assert assessment.diameter_km == 0.1
        assert assessment.velocity_km_s == 10.5
        assert assessment.absolute_magnitude == 20.5
        assert assessment.n_imp == 5
        assert assessment.impact_years == [2025, 2030, 2035]
        assert assessment.last_obs == "2023-01-01"
        assert assessment.threat_level_ru == "НИЗКИЙ (требует наблюдения)"
        assert assessment.torino_scale_ru == "Низкий риск"
        assert assessment.impact_probability_text_ru == "Низкая вероятность столкновения"
        assert assessment.energy_megatons == 10.0
        assert assessment.impact_category == "локальный"
        assert assessment.created_at == created_at
        assert assessment.updated_at == updated_at

    def test_threat_assessment_base_schema_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        data = {
            "id": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        with pytest.raises(ValidationError):
            ThreatAssessmentBase(**data)


class TestThreatAssessmentResponseSchema:
    """Unit tests for ThreatAssessmentResponse schema."""

    def test_threat_assessment_response_schema_inheritance(self):
        """Test that ThreatAssessmentResponse inherits from ThreatAssessmentBase."""
        created_at = datetime.now()
        updated_at = datetime.now()
        data = {
            "id": 1,
            "asteroid_id": 1,
            "designation": "2023 DW",
            "fullname": "2023 DW (Asteroid)",
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": 0.5,
            "diameter_km": 0.1,
            "velocity_km_s": 10.5,
            "absolute_magnitude": 20.5,
            "n_imp": 5,
            "impact_years": [2025, 2030, 2035],
            "last_obs": "2023-01-01",
            "threat_level_ru": "НИЗКИЙ (требует наблюдения)",
            "torino_scale_ru": "Низкий риск",
            "impact_probability_text_ru": "Низкая вероятность столкновения",
            "energy_megatons": 10.0,
            "impact_category": "локальный",
            "created_at": created_at,
            "updated_at": updated_at
        }

        assessment = ThreatAssessmentResponse(**data)

        assert assessment.id == 1
        assert assessment.asteroid_id == 1
        assert assessment.designation == "2023 DW"
        assert assessment.fullname == "2023 DW (Asteroid)"
        assert assessment.ip == 0.001
        assert assessment.ts_max == 1
        assert assessment.ps_max == 0.5
        assert assessment.diameter_km == 0.1
        assert assessment.velocity_km_s == 10.5
        assert assessment.absolute_magnitude == 20.5
        assert assessment.n_imp == 5
        assert assessment.impact_years == [2025, 2030, 2035]
        assert assessment.last_obs == "2023-01-01"
        assert assessment.threat_level_ru == "НИЗКИЙ (требует наблюдения)"
        assert assessment.torino_scale_ru == "Низкий риск"
        assert assessment.impact_probability_text_ru == "Низкая вероятность столкновения"
        assert assessment.energy_megatons == 10.0
        assert assessment.impact_category == "локальный"
        assert assessment.created_at == created_at
        assert assessment.updated_at == updated_at