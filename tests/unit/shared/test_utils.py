import pytest
from shared.utils.space_math import get_size_by_albedo, get_size_by_h_mag


class TestSpaceMathUtils:
    """Unit tests for space math utility functions."""

    def test_get_size_by_albedo_valid_inputs(self):
        """Test get_size_by_albedo with valid inputs."""
        # Test with typical values
        result = get_size_by_albedo(albedo=0.15, h_mag=20.0)
        expected = 1329 / (0.15 ** 0.5) * (10 ** (-0.2 * 20.0))
        
        assert result == expected
        assert isinstance(result, float)
        assert result > 0

    def test_get_size_by_albedo_edge_cases(self):
        """Test get_size_by_albedo with edge case inputs."""
        # Test with minimum valid albedo
        result_min = get_size_by_albedo(albedo=0.001, h_mag=20.0)
        assert result_min > 0
        
        # Test with maximum valid albedo
        result_max = get_size_by_albedo(albedo=1.0, h_mag=20.0)
        assert result_max > 0
        
        # Test with very bright object (negative H)
        result_bright = get_size_by_albedo(albedo=0.15, h_mag=-5.0)
        assert result_bright > 0
        
        # Test with very dim object (large positive H)
        result_dim = get_size_by_albedo(albedo=0.15, h_mag=30.0)
        assert result_dim > 0

    def test_get_size_by_albedo_invalid_albedo_zero(self):
        """Test get_size_by_albedo with zero albedo (should raise ValueError)."""
        with pytest.raises(ValueError, match="Альбедо должно быть положительным числом"):
            get_size_by_albedo(albedo=0, h_mag=20.0)

    def test_get_size_by_albedo_invalid_albedo_negative(self):
        """Test get_size_by_albedo with negative albedo (should raise ValueError)."""
        with pytest.raises(ValueError, match="Альбедо должно быть положительным числом"):
            get_size_by_albedo(albedo=-0.1, h_mag=20.0)

    def test_get_size_by_albedo_extremely_large_result(self):
        """Test get_size_by_albedo with inputs that produce extremely large results."""
        # This should trigger the "too large" validation
        with pytest.raises(ValueError, match="Calculated diameter too large"):
            get_size_by_albedo(albedo=1e-15, h_mag=-30.0)

    def test_get_size_by_albedo_extremely_small_result(self):
        """Test get_size_by_albedo with inputs that produce extremely small results."""
        # This should trigger the "too small" validation
        with pytest.raises(ValueError, match="Calculated diameter too small"):
            get_size_by_albedo(albedo=0.99, h_mag=100.0)

    def test_get_size_by_albedo_calculation_accuracy(self):
        """Test the accuracy of get_size_by_albedo calculations."""
        # Test with known values from the docstring example
        result = get_size_by_albedo(albedo=0.15, h_mag=20.0)
        expected = 1329 / (0.15 ** 0.5) * (10 ** (-0.2 * 20.0))
        
        # Calculate expected manually to double-check
        manual_calc = 1329 / (0.15 ** 0.5) * (10 ** (-4.0))
        assert abs(result - manual_calc) < 1e-10  # Allow for floating point precision

    def test_get_size_by_h_mag_valid_input(self):
        """Test get_size_by_h_mag with valid input."""
        h_mag = 20.0
        result = get_size_by_h_mag(h_mag)
        
        # Should be equivalent to calling get_size_by_albedo with standard albedo 0.15
        expected = get_size_by_albedo(albedo=0.15, h_mag=h_mag)
        
        assert result == expected
        assert isinstance(result, float)
        assert result > 0

    def test_get_size_by_h_mag_edge_cases(self):
        """Test get_size_by_h_mag with edge case inputs."""
        # Test with very bright object
        result_bright = get_size_by_h_mag(h_mag=-5.0)
        assert result_bright > 0
        
        # Test with very dim object
        result_dim = get_size_by_h_mag(h_mag=30.0)
        assert result_dim > 0

    def test_get_size_by_h_mag_calculation_consistency(self):
        """Test that get_size_by_h_mag is consistent with get_size_by_albedo."""
        test_values = [10.0, 15.5, 20.0, 25.3, 30.0]
        
        for h_val in test_values:
            result_h_func = get_size_by_h_mag(h_val)
            result_albedo_func = get_size_by_albedo(albedo=0.15, h_mag=h_val)
            
            assert abs(result_h_func - result_albedo_func) < 1e-10

    def test_get_size_by_albedo_returns_float(self):
        """Test that get_size_by_albedo always returns a float."""
        result = get_size_by_albedo(albedo=0.2, h_mag=18.5)
        assert isinstance(result, float)

    def test_get_size_by_h_mag_returns_float(self):
        """Test that get_size_by_h_mag always returns a float."""
        result = get_size_by_h_mag(h_mag=18.5)
        assert isinstance(result, float)

    def test_get_size_by_albedo_with_different_albedos_same_h(self):
        """Test that different albedos with same H give different sizes."""
        h_mag = 20.0
        
        # Lower albedo means larger calculated size
        size_low_albedo = get_size_by_albedo(albedo=0.05, h_mag=h_mag)
        size_high_albedo = get_size_by_albedo(albedo=0.25, h_mag=h_mag)
        
        # Lower albedo should result in larger size
        assert size_low_albedo > size_high_albedo

    def test_get_size_by_albedo_with_same_albedo_different_h(self):
        """Test that same albedo with different H gives different sizes."""
        albedo = 0.15
        
        # Lower H (brighter) means larger size
        size_bright = get_size_by_albedo(albedo=albedo, h_mag=15.0)
        size_dim = get_size_by_albedo(albedo=albedo, h_mag=25.0)
        
        # Brighter object (lower H) should result in larger size
        assert size_bright > size_dim

    def test_get_size_by_albedo_special_cases(self):
        """Test special mathematical cases for get_size_by_albedo."""
        # Test with H = 0 (reference magnitude)
        result_h_zero = get_size_by_albedo(albedo=0.15, h_mag=0.0)
        expected_h_zero = 1329 / (0.15 ** 0.5) * (10 ** 0)
        assert abs(result_h_zero - expected_h_zero) < 1e-10
        
        # Test with H that makes exponent zero
        result_exp_zero = get_size_by_albedo(albedo=1.0, h_mag=0.0)
        expected_exp_zero = 1329 / (1.0 ** 0.5) * (10 ** 0)
        assert abs(result_exp_zero - expected_exp_zero) < 1e-10