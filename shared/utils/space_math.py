def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """Рассчитывает диаметр астероида в км по альбедо и абсолютной звездной величине"""
    return 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))


def get_size_by_h_mag(h_mag: float) -> float:
    """Вычисляет диаметр астероида с использованием стандартного альбедо 0.15"""
    return get_size_by_albedo(0.15, h_mag)
