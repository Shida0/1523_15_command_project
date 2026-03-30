"""
Unit tests for Approach API endpoints.

These tests verify that API endpoints correctly handle requests,
pass parameters to services, and return expected responses.
"""
import pytest
from unittest.mock import AsyncMock


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


class TestApproachAPI:
    """Unit tests for Approach API endpoints."""

    def test_get_upcoming_approaches_default_params(self, client, mock_approach_service):
        """Test getting upcoming approaches with default parameters."""
        # Arrange
        mock_approach_service.get_upcoming.return_value = [
            create_approach_mock(id=1, asteroid_designation="AST1")
        ]

        # Act
        response = client.get("/api/v1/approaches/upcoming")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_approach_service.get_upcoming.assert_called_once_with(limit=10)

    def test_get_upcoming_approaches_custom_params(self, client, mock_approach_service):
        """Test getting upcoming approaches with custom parameters."""
        # Arrange
        mock_approach_service.get_upcoming.return_value = []

        # Act
        response = client.get(
            "/api/v1/approaches/upcoming",
            params={"limit": 50}
        )

        # Assert
        assert response.status_code == 200
        mock_approach_service.get_upcoming.assert_called_once_with(limit=50)

    def test_get_closest_approaches(self, client, mock_approach_service):
        """Test getting closest approaches by distance."""
        # Arrange
        mock_approach_service.get_closest.return_value = [
            create_approach_mock(id=1, distance_au=0.001, asteroid_designation="AST1"),
            create_approach_mock(id=2, distance_au=0.002, asteroid_designation="AST2")
        ]

        # Act
        response = client.get(
            "/api/v1/approaches/closest",
            params={"limit": 20, "skip": 0}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_approach_service.get_closest.assert_called_once_with(limit=20, skip=0)

    def test_get_fastest_approaches(self, client, mock_approach_service):
        """Test getting fastest approaches by velocity."""
        # Arrange
        mock_approach_service.get_fastest.return_value = [
            create_approach_mock(id=1, velocity_km_s=20.5, asteroid_designation="AST1")
        ]

        # Act
        response = client.get(
            "/api/v1/approaches/fastest",
            params={"limit": 15, "skip": 5}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_approach_service.get_fastest.assert_called_once_with(limit=15, skip=5)

    def test_get_approaches_in_period(self, client, mock_approach_service):
        """Test getting approaches in a time period."""
        # Arrange
        mock_approach_service.get_approaches_in_period.return_value = [
            create_approach_mock(approach_time="2024-06-01T00:00:00Z")
        ]

        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-12-31T23:59:59Z"

        # Act
        response = client.get(
            "/api/v1/approaches/in-period",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "skip": 0,
                "limit": 100
            }
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_approach_service.get_approaches_in_period.assert_called_once()

    def test_get_approaches_in_period_with_max_distance(self, client, mock_approach_service):
        """Test getting approaches in period with max distance filter."""
        # Arrange
        mock_approach_service.get_approaches_in_period.return_value = []

        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-12-31T23:59:59Z"

        # Act
        response = client.get(
            "/api/v1/approaches/in-period",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "max_distance": 0.05,
                "skip": 0,
                "limit": 100
            }
        )

        # Assert
        assert response.status_code == 200
        call_args = mock_approach_service.get_approaches_in_period.call_args
        assert call_args[1]["max_distance"] == 0.05

    def test_get_approaches_in_period_missing_params(self, client):
        """Test getting approaches with missing required params."""
        # Act - missing start_date and end_date
        response = client.get("/api/v1/approaches/in-period")

        # Assert
        assert response.status_code == 422

    def test_get_approach_statistics(self, client, mock_approach_service):
        """Test getting approach statistics."""
        # Arrange
        mock_approach_service.get_statistics.return_value = {
            "total_approaches": 500,
            "average_distance_au": 0.01,
            "average_velocity_km_s": 12.5
        }

        # Act
        response = client.get("/api/v1/approaches/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_approaches"] == 500
        assert data["average_distance_au"] == 0.01
        mock_approach_service.get_statistics.assert_called_once()

    def test_get_approaches_by_asteroid_id(self, client, mock_approach_service):
        """Test getting approaches by asteroid ID."""
        # Arrange
        mock_approach_service.get_by_asteroid_id.return_value = [
            create_approach_mock(id=1, asteroid_id=123)
        ]

        # Act
        response = client.get(
            "/api/v1/approaches/by-id/123",
            params={"skip": 0, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_approach_service.get_by_asteroid_id.assert_called_once_with(
            asteroid_id=123, skip=0, limit=50
        )

    def test_get_approaches_by_asteroid_designation(self, client, mock_approach_service):
        """Test getting approaches by asteroid designation."""
        # Arrange
        mock_approach_service.get_by_asteroid_designation.return_value = [
            create_approach_mock(id=1, asteroid_designation="2023 TEST")
        ]

        # Act
        response = client.get(
            "/api/v1/approaches/by-designation/2023%20TEST",
            params={"skip": 10, "limit": 25}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_approach_service.get_by_asteroid_designation.assert_called_once_with(
            designation="2023 TEST", skip=10, limit=25
        )

    def test_get_approaches_by_asteroid_empty_result(self, client, mock_approach_service):
        """Test getting approaches when none exist."""
        # Arrange
        mock_approach_service.get_by_asteroid_id.return_value = []

        # Act
        response = client.get("/api/v1/approaches/by-id/999")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_upcoming_invalid_limit(self, client):
        """Test getting upcoming approaches with invalid limit."""
        # Act - limit > 100
        response = client.get("/api/v1/approaches/upcoming", params={"limit": 200})

        # Assert
        assert response.status_code == 422

    def test_get_closest_with_pagination(self, client, mock_approach_service):
        """Test getting closest approaches with pagination."""
        # Arrange
        mock_approach_service.get_closest.return_value = [
            create_approach_mock(id=i, distance_au=0.001 * i) for i in range(1, 6)
        ]

        # Act
        response = client.get(
            "/api/v1/approaches/closest",
            params={"limit": 5, "skip": 10}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 5
        mock_approach_service.get_closest.assert_called_once_with(limit=5, skip=10)

    def test_get_fastest_with_pagination(self, client, mock_approach_service):
        """Test getting fastest approaches with pagination."""
        # Arrange
        mock_approach_service.get_fastest.return_value = [
            create_approach_mock(id=i, velocity_km_s=10.0 + i) for i in range(1, 4)
        ]

        # Act
        response = client.get(
            "/api/v1/approaches/fastest",
            params={"limit": 3, "skip": 0}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 3
        mock_approach_service.get_fastest.assert_called_once_with(limit=3, skip=0)
