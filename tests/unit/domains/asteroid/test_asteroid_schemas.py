import pytest
from pydantic import ValidationError
from datetime import datetime
from domains.asteroid.schemas.asteroid_schema import AsteroidBase, AsteroidCreate, AsteroidResponse


class TestAsteroidCreateSchema:
    """Unit tests for AsteroidCreate schema."""

    def test_asteroid_create_schema_valid_data(self):
        """Test creating asteroid with valid data passes validation."""
        data = {
            "designation": "2023 DW",
            "name": "Test Asteroid",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1,
            "accurate_diameter": True,
            "albedo": 0.15,
            "diameter_source": "measured",
            "perihelion_au": 0.8,
            "aphelion_au": 1.2,
            "earth_moid_au": 0.05
        }

        asteroid = AsteroidCreate(**data)

        assert asteroid.designation == "2023 DW"
        assert asteroid.name == "Test Asteroid"
        assert asteroid.absolute_magnitude == 20.5
        assert asteroid.estimated_diameter_km == 0.1
        assert asteroid.accurate_diameter is True
        assert asteroid.albedo == 0.15
        assert asteroid.diameter_source == "measured"
        assert asteroid.perihelion_au == 0.8
        assert asteroid.aphelion_au == 1.2
        assert asteroid.earth_moid_au == 0.05

    def test_asteroid_create_schema_with_defaults(self):
        """Test creating asteroid with default values."""
        data = {
            "designation": "2023 DW",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1
        }

        asteroid = AsteroidCreate(**data)

        assert asteroid.designation == "2023 DW"
        assert asteroid.name is None
        assert asteroid.absolute_magnitude == 20.5
        assert asteroid.estimated_diameter_km == 0.1
        assert asteroid.accurate_diameter is False  # Default value
        assert asteroid.albedo == 0.15  # Default value
        assert asteroid.diameter_source == "calculated"  # Default value

    def test_asteroid_create_schema_albedo_validation_valid_range(self):
        """Test that albedo values in valid range pass validation."""
        valid_values = [0.0, 0.1, 0.5, 0.9, 1.0]

        for value in valid_values:
            data = {
                "designation": "2023 DW",
                "absolute_magnitude": 20.5,
                "estimated_diameter_km": 0.1,
                "albedo": value
            }

            asteroid = AsteroidCreate(**data)
            assert asteroid.albedo == value

    def test_asteroid_create_schema_albedo_validation_below_range(self):
        """Test that albedo values below range raise ValidationError."""
        data = {
            "designation": "2023 DW",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1,
            "albedo": -0.1
        }

        with pytest.raises(ValidationError):
            AsteroidCreate(**data)

    def test_asteroid_create_schema_albedo_validation_above_range(self):
        """Test that albedo values above range raise ValidationError."""
        data = {
            "designation": "2023 DW",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1,
            "albedo": 1.1
        }

        with pytest.raises(ValidationError):
            AsteroidCreate(**data)

    def test_asteroid_create_schema_required_fields_missing(self):
        """Test that missing required fields raise ValidationError."""
        required_fields_tests = [
            {},  # No fields
            {"name": "Test Asteroid"},  # Missing designation, magnitude, diameter
            {"designation": "2023 DW"},  # Missing magnitude, diameter
            {"designation": "2023 DW", "absolute_magnitude": 20.5},  # Missing diameter
        ]

        for data in required_fields_tests:
            with pytest.raises(ValidationError):
                AsteroidCreate(**data)

    def test_asteroid_create_schema_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        data = {
            "designation": "2023 DW",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1,
            "name": None,
            "perihelion_au": None,
            "aphelion_au": None,
            "earth_moid_au": None,
            "orbit_id": None,
            "orbit_class": None
        }

        asteroid = AsteroidCreate(**data)

        assert asteroid.designation == "2023 DW"
        assert asteroid.name is None
        assert asteroid.perihelion_au is None
        assert asteroid.aphelion_au is None
        assert asteroid.earth_moid_au is None
        assert asteroid.orbit_id is None
        assert asteroid.orbit_class is None


class TestAsteroidBaseSchema:
    """Unit tests for AsteroidBase schema."""

    def test_asteroid_base_schema_valid_data(self):
        """Test creating asteroid base with valid data."""
        data = {
            "id": 1,
            "designation": "2023 DW",
            "name": "Test Asteroid",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1,
            "accurate_diameter": True,
            "albedo": 0.15,
            "diameter_source": "measured",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "perihelion_au": 0.8,
            "aphelion_au": 1.2,
            "earth_moid_au": 0.05
        }

        asteroid = AsteroidBase(**data)

        assert asteroid.id == 1
        assert asteroid.designation == "2023 DW"
        assert asteroid.name == "Test Asteroid"
        assert asteroid.absolute_magnitude == 20.5
        assert asteroid.estimated_diameter_km == 0.1
        assert asteroid.accurate_diameter is True
        assert asteroid.albedo == 0.15
        assert asteroid.diameter_source == "measured"
        assert asteroid.created_at
        assert asteroid.updated_at

    def test_asteroid_base_schema_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        data = {
            "id": 1,
            "name": "Test Asteroid",  # Missing designation, magnitude, diameter
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        with pytest.raises(ValidationError):
            AsteroidBase(**data)


class TestAsteroidResponseSchema:
    """Unit tests for AsteroidResponse schema."""

    def test_asteroid_response_schema_inheritance(self):
        """Test that AsteroidResponse inherits from AsteroidBase."""
        data = {
            "id": 1,
            "designation": "2023 DW",
            "name": "Test Asteroid",
            "absolute_magnitude": 20.5,
            "estimated_diameter_km": 0.1,
            "accurate_diameter": True,
            "albedo": 0.15,
            "diameter_source": "measured",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "perihelion_au": 0.8,
            "aphelion_au": 1.2,
            "earth_moid_au": 0.05
        }

        asteroid = AsteroidResponse(**data)

        assert asteroid.id == 1
        assert asteroid.designation == "2023 DW"
        assert asteroid.name == "Test Asteroid"
        assert asteroid.absolute_magnitude == 20.5
        assert asteroid.estimated_diameter_km == 0.1
        assert asteroid.accurate_diameter is True
        assert asteroid.albedo == 0.15
        assert asteroid.diameter_source == "measured"
        assert asteroid.created_at
        assert asteroid.updated_at
        assert asteroid.perihelion_au == 0.8
        assert asteroid.aphelion_au == 1.2
        assert asteroid.earth_moid_au == 0.05