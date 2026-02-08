# space_math.py
from typing import Dict, Any, Optional
from datetime import datetime

def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """
    Рассчитывает диаметр астероида в км по альбедо и абсолютной звездной величине (H).
    Формула: diameter = 1329 / sqrt(albedo) * 10^(-0.2*H)
    
    Args:
        albedo: Альбедо (отражательная способность) в диапазоне 0.0-1.0
        h_mag: Абсолютная звездная величина H
        
    Returns:
        Диаметр в километрах
    """
    # Проверка на None, 0, отрицательные значения
    if albedo is None or albedo <= 0:
        # Стандартное значение альбедо 0.15 для PHA
        albedo = 0.15
    elif albedo > 1.0:
        # Ограничиваем верхнюю границу альбедо
        albedo = 1.0
    
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
        # Обработка исключения ZeroDivisionError
        # Стандартное значение альбедо 0.15 для PHA
        albedo = 0.15
        result = 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))
        return result

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

