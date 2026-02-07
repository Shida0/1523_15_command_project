# space_math.py
from typing import Dict, Any, Optional
from datetime import datetime

def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """Вычисляет диаметр астероида на основе альбедо и абсолютной звёздной величины.
    
    Args:
        albedo: Альбедо (отражательная способность) астероида (0 < albedo <= 1)
        h_mag: Абсолютная звёздная величина (H)
        
    Returns:
        Расчетный диаметр в километрах
        
    Raises:
        ValueError: Если albedo <= 0
        
    Example:
        >>> get_size_by_albedo(0.15, 20.0)
        0.1329
    """
    if albedo <= 0:
        raise ValueError(f"Альбедо должно быть положительным числом. Получено: {albedo}")
    
    try:
        result = 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))
        
        # Check for overflow or invalid values
        if result <= 0 or not isinstance(result, (int, float)) or result != result:  # result != result checks for NaN
            raise ValueError(f"Invalid result calculated: {result}")
        
        # Clamp extremely large or small values
        if result > 1e10:  # Very large asteroid
            raise ValueError(f"Calculated diameter too large: {result}")
        if result < 1e-10:  # Very small asteroid
            raise ValueError(f"Calculated diameter too small: {result}")
            
        return result
    except (OverflowError, ZeroDivisionError, ValueError) as e:
        raise ValueError(f"Error calculating size by albedo: {e}")

def get_size_by_h_mag(h_mag: float) -> float:
    """Вычисляет диаметр астероида с использованием стандартного альбедо 0.15.
    
    Args:
        h_mag: Абсолютная звёздная величина (H)
        
    Returns:
        Расчетный диаметр в километрах
        
    Example:
        >>> get_size_by_h_mag(20.0)
        0.1329
    """
    assumed_albedo = 0.15
    return get_size_by_albedo(assumed_albedo, h_mag)

