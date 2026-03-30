import pytest
from datetime import datetime
from domains.approach.models.close_approach import CloseApproachModel


class TestApproachModel:
    """Unit tests for CloseApproachModel class."""

    def test_approach_model_creation_with_valid_data(self):
        """Test creating a close approach model with valid data."""
        approach = CloseApproachModel(
            asteroid_id=1,
            approach_time=datetime.now(),
            distance_au=0.01,
            distance_km=1495978.707,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW",
            asteroid_name="Test Asteroid"
        )

        assert approach.asteroid_id == 1
        assert approach.distance_au == 0.01
        assert approach.distance_km == 1495978.707
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name == "Test Asteroid"

    def test_approach_model_creation_with_defaults(self):
        """Test creating a close approach model with minimal required data."""
        approach_time = datetime.now()
        approach = CloseApproachModel(
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW"
        )

        assert approach.asteroid_id == 1
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.01
        assert approach.velocity_km_s == 10.5
        assert approach.asteroid_designation == "2023 DW"
        assert approach.asteroid_name is None
        assert approach.data_source == "NASA CAD API"  # Default value

    def test_approach_model_distance_calculation(self):
        """Test that distance_km is automatically calculated from distance_au."""
        approach_time = datetime.now()
        approach = CloseApproachModel(
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,  # 0.01 AU
            velocity_km_s=10.5,
            asteroid_designation="2023 DW"
        )

        expected_distance_km = 0.01 * 149597870.7  # Convert AU to km
        assert approach.distance_km == expected_distance_km

    def test_approach_model_distance_calculation_not_overridden(self):
        """Test that provided distance_km is not overridden by calculation."""
        approach_time = datetime.now()
        provided_distance_km = 2000000.0
        approach = CloseApproachModel(
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,
            distance_km=provided_distance_km,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW"
        )

        # Should use the provided distance_km, not calculate from distance_au
        assert approach.distance_km == provided_distance_km

    def test_approach_model_data_source_default(self):
        """Test that data_source defaults to 'NASA CAD API' when not provided."""
        approach_time = datetime.now()
        approach = CloseApproachModel(
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW"
        )

        assert approach.data_source == "NASA CAD API"

    def test_approach_model_data_source_custom(self):
        """Test that custom data_source is preserved."""
        approach_time = datetime.now()
        approach = CloseApproachModel(
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW",
            data_source="Custom Source"
        )

        assert approach.data_source == "Custom Source"

    def test_approach_model_repr(self):
        """Test string representation of approach model."""
        approach_time = datetime(2023, 1, 1, 12, 0, 0)
        approach = CloseApproachModel(
            id=1,
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW",
            asteroid_name="Test Asteroid"
        )

        expected_repr = f"CloseApproachModel(id=1, asteroid=2023 DW, time={approach_time})"
        assert repr(approach) == expected_repr

    def test_approach_model_repr_without_name(self):
        """Test string representation of approach model without name."""
        approach_time = datetime(2023, 1, 1, 12, 0, 0)
        approach = CloseApproachModel(
            id=1,
            asteroid_id=1,
            approach_time=approach_time,
            distance_au=0.01,
            velocity_km_s=10.5,
            asteroid_designation="2023 DW"
        )

        expected_repr = f"CloseApproachModel(id=1, asteroid=2023 DW, time={approach_time})"
        assert repr(approach) == expected_repr