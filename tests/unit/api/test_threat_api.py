"""
Unit tests for Threat API endpoints.

These tests verify that API endpoints correctly handle requests,
pass parameters to services, and return expected responses.
"""
import pytest
from unittest.mock import AsyncMock


class TestThreatAPI:
    """Unit tests for Threat API endpoints."""

    def test_get_current_threats_default_params(self, client, mock_threat_service):
        """Test getting current threats with default parameters."""
        # Arrange
        mock_threat_service.get_by_risk_level.return_value = [
            {"designation": "AST1", "ts_max": 3, "ip": 0.01}
        ]

        # Act
        response = client.get("/api/v1/threats/current")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_threat_service.get_by_risk_level.assert_called_once_with(
            min_ts=0, max_ts=10, skip=0, limit=100
        )

    def test_get_current_threats_custom_params(self, client, mock_threat_service):
        """Test getting current threats with custom Torino scale filter."""
        # Arrange
        mock_threat_service.get_by_risk_level.return_value = [
            {"designation": "AST1", "ts_max": 5}
        ]

        # Act
        response = client.get(
            "/api/v1/threats/current",
            params={"min_ts": 3, "skip": 0, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        mock_threat_service.get_by_risk_level.assert_called_once_with(
            min_ts=3, max_ts=10, skip=0, limit=50
        )

    def test_get_high_risk_threats_default_params(self, client, mock_threat_service):
        """Test getting high risk threats with default parameters."""
        # Arrange
        mock_threat_service.get_high_risk.return_value = [
            {"designation": "DANGER1", "ts_max": 7, "ip": 0.5},
            {"designation": "DANGER2", "ts_max": 6, "ip": 0.3}
        ]

        # Act
        response = client.get("/api/v1/threats/high-risk")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_threat_service.get_high_risk.assert_called_once_with(limit=20, skip=0)

    def test_get_high_risk_threats_custom_params(self, client, mock_threat_service):
        """Test getting high risk threats with custom parameters."""
        # Arrange
        mock_threat_service.get_high_risk.return_value = []

        # Act
        response = client.get(
            "/api/v1/threats/high-risk",
            params={"limit": 10, "skip": 5}
        )

        # Assert
        assert response.status_code == 200
        mock_threat_service.get_high_risk.assert_called_once_with(limit=10, skip=5)

    def test_get_threats_by_probability(self, client, mock_threat_service):
        """Test getting threats by probability range."""
        # Arrange
        mock_threat_service.get_by_probability.return_value = [
            {"designation": "PROB1", "ip": 0.005}
        ]

        # Act
        response = client.get(
            "/api/v1/threats/by-probability",
            params={
                "min_probability": 0.001,
                "max_probability": 0.01,
                "skip": 0,
                "limit": 100
            }
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_threat_service.get_by_probability.assert_called_once()

    def test_get_threats_by_energy(self, client, mock_threat_service):
        """Test getting threats by energy range."""
        # Arrange
        mock_threat_service.get_by_energy.return_value = [
            {"designation": "ENERGY1", "energy_megatons": 100.0}
        ]

        # Act
        response = client.get(
            "/api/v1/threats/by-energy",
            params={
                "min_energy": 50.0,
                "max_energy": 200.0,
                "skip": 0,
                "limit": 100
            }
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_threat_service.get_by_energy.assert_called_once()

    def test_get_threats_by_energy_no_max(self, client, mock_threat_service):
        """Test getting threats by energy with no max limit."""
        # Arrange
        mock_threat_service.get_by_energy.return_value = []

        # Act
        response = client.get(
            "/api/v1/threats/by-energy",
            params={"min_energy": 100.0, "skip": 0, "limit": 100}
        )

        # Assert
        assert response.status_code == 200
        call_args = mock_threat_service.get_by_energy.call_args
        assert call_args[1]["min_energy"] == 100.0
        assert call_args[1]["max_energy"] is None

    def test_get_threat_statistics(self, client, mock_threat_service):
        """Test getting threat statistics."""
        # Arrange
        mock_threat_service.get_statistics.return_value = {
            "total_threats": 50,
            "high_risk_count": 5,
            "average_probability": 0.002
        }

        # Act
        response = client.get("/api/v1/threats/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_threats"] == 50
        assert data["high_risk_count"] == 5
        mock_threat_service.get_statistics.assert_called_once()

    def test_get_threat_by_designation_found(self, client, mock_threat_service):
        """Test getting threat by designation when it exists."""
        # Arrange
        threat_data = {
            "designation": "2023 TEST",
            "ts_max": 2,
            "ip": 0.001,
            "energy_megatons": 10.0
        }
        mock_threat_service.get_by_designation = AsyncMock(return_value=threat_data)

        # Act
        response = client.get("/api/v1/threats/2023%20TEST")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "2023 TEST"
        assert data["ts_max"] == 2
        mock_threat_service.get_by_designation.assert_called_once_with("2023 TEST")

    def test_get_threat_by_designation_not_found(self, client, mock_threat_service):
        """Test getting threat by designation when it doesn't exist.
        
        Note: The API returns 200 with null/None when threat is not found.
        This is the expected behavior - the endpoint returns Optional[dict].
        """
        # Arrange
        mock_threat_service.get_by_designation = AsyncMock(return_value=None)

        # Act
        response = client.get("/api/v1/threats/NONEXISTENT")

        # Assert
        assert response.status_code == 200
        assert response.json() is None
        mock_threat_service.get_by_designation.assert_called_once_with("NONEXISTENT")

    def test_get_threats_by_category(self, client, mock_threat_service):
        """Test getting threats by impact category."""
        # Arrange
        mock_threat_service.get_by_category.return_value = [
            {"designation": "CAT1", "impact_category": "локальный"}
        ]

        # Act
        response = client.get(
            "/api/v1/threats/by-category/локальный",
            params={"skip": 0, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_threat_service.get_by_category.assert_called_once_with(
            category="локальный", skip=0, limit=50
        )

    def test_get_current_threats_pagination(self, client, mock_threat_service):
        """Test getting current threats with pagination."""
        # Arrange
        mock_threat_service.get_by_risk_level.return_value = [
            {"designation": f"THR{i}", "ts_max": 3} for i in range(10)
        ]

        # Act
        response = client.get(
            "/api/v1/threats/current",
            params={"skip": 20, "limit": 10, "min_ts": 1}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 10
        mock_threat_service.get_by_risk_level.assert_called_once_with(
            min_ts=1, max_ts=10, skip=20, limit=10
        )

    def test_get_high_risk_invalid_limit(self, client):
        """Test getting high risk threats with invalid limit."""
        # Act - limit > 100
        response = client.get("/api/v1/threats/high-risk", params={"limit": 150})

        # Assert
        assert response.status_code == 422

    def test_get_current_invalid_torino_scale(self, client):
        """Test getting current threats with invalid Torino scale."""
        # Act - min_ts > 10
        response = client.get("/api/v1/threats/current", params={"min_ts": 15})

        # Assert
        assert response.status_code == 422

    def test_get_threats_by_probability_invalid_range(self, client):
        """Test getting threats with invalid probability range."""
        # Act - probability > 1.0
        response = client.get(
            "/api/v1/threats/by-probability",
            params={"min_probability": 1.5, "max_probability": 2.0}
        )

        # Assert
        assert response.status_code == 422

    def test_get_threats_by_energy_negative(self, client):
        """Test getting threats with negative energy."""
        # Act - negative energy
        response = client.get(
            "/api/v1/threats/by-energy",
            params={"min_energy": -10.0}
        )

        # Assert
        assert response.status_code == 422

    def test_get_threats_by_category_with_pagination(self, client, mock_threat_service):
        """Test getting threats by category with pagination."""
        # Arrange
        mock_threat_service.get_by_category.return_value = [
            {"designation": f"CAT{i}", "impact_category": "региональный"}
            for i in range(3)
        ]

        # Act
        response = client.get(
            "/api/v1/threats/by-category/региональный",
            params={"skip": 5, "limit": 3}
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 3
        mock_threat_service.get_by_category.assert_called_once_with(
            category="региональный", skip=5, limit=3
        )

    def test_get_current_threats_empty_result(self, client, mock_threat_service):
        """Test getting current threats when none exist."""
        # Arrange
        mock_threat_service.get_by_risk_level.return_value = []

        # Act
        response = client.get("/api/v1/threats/current")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_high_risk_empty_result(self, client, mock_threat_service):
        """Test getting high risk threats when none exist."""
        # Arrange
        mock_threat_service.get_high_risk.return_value = []

        # Act
        response = client.get("/api/v1/threats/high-risk")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_all_endpoints_use_correct_paths(self):
        """Test that all endpoints are registered with correct paths."""
        # Import app here to avoid circular imports
        from main import app
        
        # Get all registered routes
        routes = {route.path for route in app.routes if hasattr(route, 'path')}

        # Check all threat endpoints exist
        assert "/api/v1/threats/current" in routes
        assert "/api/v1/threats/high-risk" in routes
        assert "/api/v1/threats/by-probability" in routes
        assert "/api/v1/threats/by-energy" in routes
        assert "/api/v1/threats/statistics" in routes
        assert "/api/v1/threats/{designation}" in routes
        assert "/api/v1/threats/by-category/{category}" in routes
