def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """Рассчитывает диаметр астероида в км по альбедо и абсолютной звездной величине."""
    if albedo is None or albedo <= 0:
        albedo = 0.15
    elif albedo > 1.0:
        albedo = 1.0

    try:
        result = 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))

        if result <= 0 or not isinstance(result, (int, float)) or result != result:
            raise ValueError(f"Invalid result calculated: {result}")

        if result > 1e10:
            raise ValueError(f"Calculated diameter too large: {result}")
        if result < 1e-10:
            raise ValueError(f"Calculated diameter too small: {result}")

        return result
    except (OverflowError, ZeroDivisionError, ValueError) as e:
        albedo = 0.15
        result = 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))
        return result


def get_size_by_h_mag(h_mag: float) -> float:
    """Вычисляет диаметр астероида с использованием стандартного альбедо 0.15."""
    assumed_albedo = 0.15
    return get_size_by_albedo(assumed_albedo, h_mag)
