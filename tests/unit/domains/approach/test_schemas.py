import pytest
from pydantic import ValidationError
from datetime import datetime
from domains.approach.schemas.approach_schema import ApproachBase, ApproachCreate, ApproachResponse


class TestApproachCreateSchema:
    """Unit tests for ApproachCreate schema."""

    def test_approach_create_schema_valid_data(self):
        """Test creating approach with valid data passes validation."""
        data = {
            "asteroid_id": 1,
            "approach_time": datetime.now(),
            "distance_au": 0.01,
            "velocity_km_s": 10.5,
            "asteroid_designation": "2023 DW"
        }

        approach = ApproachCreate(**data)

        assert approach.asteroid_id == 1
        assert approach.distance_au == 0.01
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.data_source == "NASA CAD API"  # Default value

    def test_approach_create_schema_with_optional_fields(self):
        """Test creating approach with optional fields."""
        approach_time = datetime.now()
        data = {
            "asteroid_id": 1,
            "approach_time": approach_time,
            "distance_au": 0.01,
            "velocity_km_s": 10.5,
            "asteroid_designation": "2023 DW",
            "asteroid_name": "Test Asteroid",
            "data_source": "Custom Source",
            "calculation_batch_id": "batch_123"
        }

        approach = ApproachCreate(**data)

        assert approach.asteroid_id == 1
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.01
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name == "Test Asteroid"
        assert approach.data_source == "Custom Source"
        assert approach.calculation_batch_id == "batch_123"

    def test_approach_create_schema_with_defaults(self):
        """Test creating approach with default values."""
        approach_time = datetime.now()
        data = {
            "asteroid_id": 1,
            "approach_time": approach_time,
            "distance_au": 0.01,
            "velocity_km_s": 10.5,
            "asteroid_designation": "2023 DW"
        }

        approach = ApproachCreate(**data)

        assert approach.asteroid_id == 1
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.01
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name is None  # Optional field defaults to None
        assert approach.data_source == "NASA CAD API"  # Default value
        assert approach.calculation_batch_id is None  # Optional field defaults to None

    def test_approach_create_schema_required_fields_missing(self):
        """Test that missing required fields raise ValidationError."""
        required_fields_tests = [
            {},  # No fields
            {"asteroid_name": "Test Asteroid"},  # Missing all required fields
            {"asteroid_id": 1},  # Missing approach_time, distance_au, velocity_km_s, asteroid_designation
            {"asteroid_id": 1, "approach_time": datetime.now()},  # Missing distance_au, velocity_km_s, asteroid_designation
        ]

        for data in required_fields_tests:
            with pytest.raises(ValidationError):
                ApproachCreate(**data)

    def test_approach_create_schema_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        approach_time = datetime.now()
        data = {
            "asteroid_id": 1,
            "approach_time": approach_time,
            "distance_au": 0.01,
            "velocity_km_s": 10.5,
            "asteroid_designation": "2023 DW",
            "asteroid_name": None,
            "calculation_batch_id": None
        }

        approach = ApproachCreate(**data)

        assert approach.asteroid_id == 1
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.01
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name is None
        assert approach.calculation_batch_id is None


class TestApproachBaseSchema:
    """Unit tests for ApproachBase schema."""

    def test_approach_base_schema_valid_data(self):
        """Test creating approach base with valid data."""
        approach_time = datetime.now()
        created_at = datetime.now()
        updated_at = datetime.now()
        data = {
            "id": 1,
            "asteroid_id": 1,
            "approach_time": approach_time,
            "distance_au": 0.01,
            "distance_km": 1495978.707,
            "velocity_km_s": 10.5,
            "asteroid_designation": "2023 DW",
            "asteroid_name": "Test Asteroid",
            "data_source": "NASA CAD API",
            "calculation_batch_id": "batch_123",
            "created_at": created_at,
            "updated_at": updated_at
        }

        approach = ApproachBase(**data)

        assert approach.id == 1
        assert approach.asteroid_id == 1
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.01
        assert approach.distance_km == 1495978.707
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name == "Test Asteroid"
        assert approach.data_source == "NASA CAD API"
        assert approach.calculation_batch_id == "batch_123"
        assert approach.created_at == created_at
        assert approach.updated_at == updated_at

    def test_approach_base_schema_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        data = {
            "id": 1,
            "asteroid_name": "Test Asteroid",  # Missing asteroid_id, approach_time, distance_au, distance_km, velocity_km_s, asteroid_designation, data_source
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        with pytest.raises(ValidationError):
            ApproachBase(**data)


class TestApproachResponseSchema:
    """Unit tests for ApproachResponse schema."""

    def test_approach_response_schema_inheritance(self):
        """Test that ApproachResponse inherits from ApproachBase."""
        approach_time = datetime.now()
        created_at = datetime.now()
        updated_at = datetime.now()
        data = {
            "id": 1,
            "asteroid_id": 1,
            "approach_time": approach_time,
            "distance_au": 0.01,
            "distance_km": 1495978.707,
            "velocity_km_s": 10.5,
            "asteroid_designation": "2023 DW",
            "asteroid_name": "Test Asteroid",
            "data_source": "NASA CAD API",
            "calculation_batch_id": "batch_123",
            "created_at": created_at,
            "updated_at": updated_at
        }

        approach = ApproachResponse(**data)

        assert approach.id == 1
        assert approach.asteroid_id == 1
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.01
        assert approach.distance_km == 1495978.707
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name == "Test Asteroid"
        assert approach.data_source == "NASA CAD API"
        assert approach.calculation_batch_id == "batch_123"
        assert approach.created_at == created_at
        assert approach.updated_at == updated_at