"""
Unit tests for Asteroid API endpoints.

These tests verify that API endpoints correctly handle requests,
pass parameters to services, and return expected responses.
"""
import pytest
from unittest.mock import AsyncMock


# Helper function to create complete asteroid mock data
def create_asteroid_mock(designation="2023 TEST", **kwargs):
    """Create complete asteroid data matching the schema."""
    data = {
        "designation": designation,
        "name": kwargs.get("name", "Test Asteroid"),
        "perihelion_au": kwargs.get("perihelion_au", 0.9),
        "aphelion_au": kwargs.get("aphelion_au", 1.5),
        "earth_moid_au": kwargs.get("earth_moid_au", 0.03),
        "absolute_magnitude": kwargs.get("absolute_magnitude", 20.5),
        "estimated_diameter_km": kwargs.get("estimated_diameter_km", 0.15),
        "accurate_diameter": kwargs.get("accurate_diameter", False),
        "albedo": kwargs.get("albedo", 0.15),
        "diameter_source": kwargs.get("diameter_source", "calculated"),
        "orbit_id": kwargs.get("orbit_id", None),
        "orbit_class": kwargs.get("orbit_class", "Apollo"),
        "id": kwargs.get("id", 1),
        "created_at": kwargs.get("created_at", "2024-01-01T00:00:00Z"),
        "updated_at": kwargs.get("updated_at", "2024-01-01T00:00:00Z")
    }
    return data


# Helper function to create approach mock data
def create_approach_mock(**kwargs):
    """Create complete approach data matching the schema."""
    return {
        "id": kwargs.get("id", 1),
        "asteroid_id": kwargs.get("asteroid_id", 1),
        "approach_time": kwargs.get("approach_time", "2024-01-01T00:00:00Z"),
        "distance_au": kwargs.get("distance_au", 0.002),
        "distance_km": kwargs.get("distance_km", 299195.74),
        "velocity_km_s": kwargs.get("velocity_km_s", 10.5),
        "asteroid_designation": kwargs.get("asteroid_designation", "2023 TEST"),
        "asteroid_name": kwargs.get("asteroid_name", "Test Asteroid"),
        "data_source": kwargs.get("data_source", "NASA CAD API"),
        "calculation_batch_id": kwargs.get("calculation_batch_id", None),
        "created_at": kwargs.get("created_at", "2024-01-01T00:00:00Z"),
        "updated_at": kwargs.get("updated_at", "2024-01-01T00:00:00Z")
    }


# Helper function to create threat mock data
def create_threat_mock(**kwargs):
    """Create complete threat data matching the schema."""
    return {
        "id": kwargs.get("id", 1),
        "asteroid_id": kwargs.get("asteroid_id", 1),
        "designation": kwargs.get("designation", "2023 TEST"),
        "fullname": kwargs.get("fullname", "2023 TEST (Test)"),
        "ip": kwargs.get("ip", 0.001),
        "ts_max": kwargs.get("ts_max", 1),
        "ps_max": kwargs.get("ps_max", -2.5),
        "diameter_km": kwargs.get("diameter_km", 0.15),
        "velocity_km_s": kwargs.get("velocity_km_s", 10.5),
        "absolute_magnitude": kwargs.get("absolute_magnitude", 20.5),
        "n_imp": kwargs.get("n_imp", 1),
        "impact_years": kwargs.get("impact_years", [2024]),
        "last_obs": kwargs.get("last_obs", "2023-12-01"),
        "threat_level_ru": kwargs.get("threat_level_ru", "НИЗКИЙ"),
        "torino_scale_ru": kwargs.get("torino_scale_ru", "1 — Нормальный"),
        "impact_probability_text_ru": kwargs.get("impact_probability_text_ru", "0.1%"),
        "energy_megatons": kwargs.get("energy_megatons", 10.0),
        "impact_category": kwargs.get("impact_category", "локальный"),
        "created_at": kwargs.get("created_at", "2024-01-01T00:00:00Z"),
        "updated_at": kwargs.get("updated_at", "2024-01-01T00:00:00Z")
    }


class TestAsteroidAPI:
    """Unit tests for Asteroid API endpoints."""

    def test_get_near_earth_asteroids_default_params(self, client, mock_asteroid_service):
        """Test getting near-Earth asteroids with default parameters."""
        # Arrange
        mock_asteroid_service.get_by_moid.return_value = [
            create_asteroid_mock(designation="2023 TEST", earth_moid_au=0.03)
        ]

        # Act
        response = client.get("/api/v1/asteroids/near-earth")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_asteroid_service.get_by_moid.assert_called_once_with(
            max_moid=0.05, skip=0, limit=100
        )

    def test_get_near_earth_asteroids_custom_params(self, client, mock_asteroid_service):
        """Test getting near-Earth asteroids with custom parameters."""
        # Arrange
        mock_asteroid_service.get_by_moid.return_value = []

        # Act
        response = client.get(
            "/api/v1/asteroids/near-earth",
            params={"max_moid": 0.02, "skip": 10, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        mock_asteroid_service.get_by_moid.assert_called_once_with(
            max_moid=0.02, skip=10, limit=50
        )

    def test_get_all_asteroids(self, client, mock_asteroid_service):
        """Test getting all asteroids."""
        # Arrange
        mock_asteroid_service.get_by_moid.return_value = [
            create_asteroid_mock(designation="AST1"),
            create_asteroid_mock(designation="AST2")
        ]

        # Act
        response = client.get("/api/v1/asteroids/all", params={"skip": 0, "limit": 100})

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_asteroid_service.get_by_moid.assert_called_once_with(
            max_moid=1.0, skip=0, limit=100
        )

    def test_get_asteroids_by_orbit_class(self, client, mock_asteroid_service):
        """Test getting asteroids by orbit class."""
        # Arrange
        mock_asteroid_service.get_by_orbit_class.return_value = [
            create_asteroid_mock(designation="APOLLO1", orbit_class="Apollo")
        ]

        # Act
        response = client.get(
            "/api/v1/asteroids/orbit-class/Apollo",
            params={"skip": 0, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_asteroid_service.get_by_orbit_class.assert_called_once_with(
            "Apollo", skip=0, limit=50
        )

    def test_get_asteroids_with_accurate_diameter(self, client, mock_asteroid_service):
        """Test getting asteroids with accurate diameter."""
        # Arrange
        mock_asteroid_service.get_with_accurate_diameter.return_value = [
            create_asteroid_mock(designation="ACC1", accurate_diameter=True)
        ]

        # Act
        response = client.get(
            "/api/v1/asteroids/accurate-diameter",
            params={"skip": 0, "limit": 100}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_asteroid_service.get_with_accurate_diameter.assert_called_once_with(
            skip=0, limit=100
        )

    def test_get_asteroid_statistics(self, client, mock_asteroid_service):
        """Test getting asteroid statistics."""
        # Arrange
        mock_asteroid_service.get_statistics.return_value = {
            "total_asteroids": 100,
            "average_diameter_km": 0.5
        }

        # Act
        response = client.get("/api/v1/asteroids/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_asteroids"] == 100
        assert data["average_diameter_km"] == 0.5
        mock_asteroid_service.get_statistics.assert_called_once()

    def test_get_asteroid_by_designation_found(self, client, mock_asteroid_service, mock_approach_service, mock_threat_service):
        """Test getting detailed asteroid info when asteroid exists."""
        # Arrange
        asteroid_data = create_asteroid_mock()
        approaches_data = [create_approach_mock()]
        threat_data = create_threat_mock()

        mock_asteroid_service.get_by_designation = AsyncMock(return_value=asteroid_data)
        mock_approach_service.get_by_asteroid_designation = AsyncMock(return_value=approaches_data)
        mock_threat_service.get_by_designation = AsyncMock(return_value=threat_data)

        # Act
        response = client.get("/api/v1/asteroids/2023%20TEST")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "2023 TEST"
        assert len(data["close_approaches"]) == 1
        assert data["threat_assessment"] is not None

        # Verify all services were called
        mock_asteroid_service.get_by_designation.assert_called_once_with("2023 TEST")
        # Note: API doesn't pass skip/limit to get_by_asteroid_designation
        mock_approach_service.get_by_asteroid_designation.assert_called_once_with(
            "2023 TEST"
        )
        mock_threat_service.get_by_designation.assert_called_once_with("2023 TEST")

    def test_get_asteroid_by_designation_not_found(self, client, mock_asteroid_service):
        """Test getting asteroid that doesn't exist."""
        # Arrange
        mock_asteroid_service.get_by_designation = AsyncMock(return_value=None)

        # Act
        response = client.get("/api/v1/asteroids/NONEXISTENT")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        mock_asteroid_service.get_by_designation.assert_called_once_with("NONEXISTENT")

    def test_get_asteroid_by_designation_no_approaches(self, client, mock_asteroid_service, mock_approach_service, mock_threat_service):
        """Test getting asteroid with no close approaches."""
        # Arrange
        asteroid_data = create_asteroid_mock()
        mock_asteroid_service.get_by_designation = AsyncMock(return_value=asteroid_data)
        mock_approach_service.get_by_asteroid_designation = AsyncMock(return_value=[])
        mock_threat_service.get_by_designation = AsyncMock(return_value=None)

        # Act
        response = client.get("/api/v1/asteroids/2023%20TEST")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["close_approaches"] == []
        assert data["threat_assessment"] is None

    def test_get_near_earth_invalid_params(self, client):
        """Test getting near-Earth asteroids with invalid parameters."""
        # Act - negative skip should return 422
        response = client.get(
            "/api/v1/asteroids/near-earth",
            params={"skip": -1, "limit": 100}
        )

        # Assert
        assert response.status_code == 422

    def test_get_near_earth_limit_too_high(self, client):
        """Test getting near-Earth asteroids with limit > 1000."""
        # Act
        response = client.get(
            "/api/v1/asteroids/near-earth",
            params={"limit": 2000}
        )

        # Assert
        assert response.status_code == 422

    def test_get_asteroids_by_orbit_class_with_pagination(self, client, mock_asteroid_service):
        """Test getting asteroids by orbit class with pagination."""
        # Arrange
        mock_asteroid_service.get_by_orbit_class.return_value = [
            create_asteroid_mock(designation=f"AST{i}", orbit_class="Aten") for i in range(5)
        ]

        # Act
        response = client.get(
            "/api/v1/asteroids/orbit-class/Aten",
            params={"skip": 10, "limit": 5}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 5
        mock_asteroid_service.get_by_orbit_class.assert_called_once_with(
            "Aten", skip=10, limit=5
        )
