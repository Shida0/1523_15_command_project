import pytest
from datetime import datetime
from decimal import Decimal
from domains.asteroid.models.asteroid import AsteroidModel


class TestAsteroidModel:
    """Unit tests for AsteroidModel class."""

    def test_asteroid_model_creation_with_valid_data(self):
        """Test creating an asteroid model with valid data."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            name="Test Asteroid",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0.15,
            accurate_diameter=True,
            diameter_source="measured"
        )

        assert asteroid.designation == "2023 DW"
        assert asteroid.name == "Test Asteroid"
        assert asteroid.absolute_magnitude == 20.5
        assert asteroid.estimated_diameter_km == 0.1
        assert asteroid.albedo == 0.15
        assert asteroid.accurate_diameter is True
        assert asteroid.diameter_source == "measured"

    def test_asteroid_model_creation_with_defaults(self):
        """Test creating an asteroid model with minimal required data."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0.15
        )

        assert asteroid.designation == "2023 DW"
        assert asteroid.name is None
        assert asteroid.absolute_magnitude == 20.5
        assert asteroid.estimated_diameter_km == 0.1
        assert asteroid.albedo == 0.15
        assert asteroid.diameter_source == "calculated"  # Default value

    def test_asteroid_model_albedo_validation_default(self):
        """Test that albedo defaults to 0.15 when not provided."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1
        )

        assert asteroid.albedo == 0.15

    def test_asteroid_model_albedo_validation_out_of_range_high(self):
        """Test that albedo > 1 is corrected to default value."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=1.5
        )

        assert asteroid.albedo == 0.15

    def test_asteroid_model_albedo_validation_out_of_range_low(self):
        """Test that albedo <= 0 is corrected to default value."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0
        )

        assert asteroid.albedo == 0.15

    def test_asteroid_model_albedo_validation_conversion(self):
        """Test that string albedo is converted to float."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo="0.2"
        )

        assert asteroid.albedo == 0.2

    def test_asteroid_model_diameter_source_validation_invalid(self):
        """Test that invalid diameter_source is corrected to default."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0.15,
            diameter_source="invalid"
        )

        assert asteroid.diameter_source == "calculated"

    def test_asteroid_model_diameter_source_validation_valid_options(self):
        """Test that all valid diameter_source options are accepted."""
        valid_sources = ["measured", "computed", "calculated"]
        
        for source in valid_sources:
            asteroid = AsteroidModel(
                designation=f"2023 DW-{source}",
                absolute_magnitude=20.5,
                estimated_diameter_km=0.1,
                albedo=0.15,
                diameter_source=source
            )
            
            assert asteroid.diameter_source == source

    def test_asteroid_model_diameter_validation_default(self):
        """Test that diameter defaults to 0.05 when not provided."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            albedo=0.15
        )

        assert asteroid.estimated_diameter_km == 0.05

    def test_asteroid_model_diameter_validation_negative(self):
        """Test that negative diameter is corrected to default value."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=-1.0,
            albedo=0.15
        )

        assert asteroid.estimated_diameter_km == 0.05

    def test_asteroid_model_diameter_validation_zero(self):
        """Test that zero diameter is corrected to default value."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0,
            albedo=0.15
        )

        assert asteroid.estimated_diameter_km == 0.05

    def test_asteroid_model_absolute_magnitude_validation_default(self):
        """Test that absolute_magnitude defaults to 18.0 when not provided."""
        asteroid = AsteroidModel(
            designation="2023 DW",
            estimated_diameter_km=0.1,
            albedo=0.15
        )

        assert asteroid.absolute_magnitude == 18.0

    def test_asteroid_model_repr(self):
        """Test string representation of asteroid model."""
        asteroid = AsteroidModel(
            id=1,
            designation="2023 DW",
            name="Test Asteroid",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0.15
        )

        expected_repr = "AsteroidModel(id=1, designation=2023 DW, name=Test Asteroid)"
        assert repr(asteroid) == expected_repr

    def test_asteroid_model_repr_without_name(self):
        """Test string representation of asteroid model without name."""
        asteroid = AsteroidModel(
            id=1,
            designation="2023 DW",
            absolute_magnitude=20.5,
            estimated_diameter_km=0.1,
            albedo=0.15
        )

        expected_repr = "AsteroidModel(id=1, designation=2023 DW, name=None)"
        assert repr(asteroid) == expected_repr