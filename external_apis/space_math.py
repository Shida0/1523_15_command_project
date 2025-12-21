from typing import Dict, Any, Optional
from datetime import datetime

def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """Вычисляет диаметр астероида на основе альбедо и абсолютной звёздной величины."""
    if albedo <= 0:
        raise ValueError(f"Альбедо должно быть положительным числом. Получено: {albedo}")
    return 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))

def get_size_by_h_mag(h_mag: float) -> float:
    """Вычисляет диаметр астероида с использованием стандартного альбедо."""
    assumed_albedo = 0.15
    return get_size_by_albedo(assumed_albedo, h_mag)
