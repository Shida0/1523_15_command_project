import math

def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """Вычисляет диаметр астероида на основе альбедо и абсолютной звёздной величины."""
    return 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))


def get_size_by_h_mag(h_mag: float) -> float:
    """Вычисляет диаметр астероида с использованием стандартного альбедо."""
    assumed_albedo = 0.15  # Стандартное предположение для каменных астероидов
    return get_size_by_albedo(assumed_albedo, h_mag)


def count_danger(diameter_km, distance_au, velocity_km_s):
    """
    Оценивает опасность астероида на основе диаметра, расстояния до Земли и скорости.
    
    Args:
        diameter_km (float): Диаметр астероида в километрах
        distance_au (float): Расстояние до Земли в астрономических единицах
        velocity_km_s (float): Относительная скорость в км/с
    
    Returns:
        dict: Словарь с исходными данными, оценкой угрозы и ущерба
    """
    
    # Преобразование расстояния в километры
    distance_km = distance_au * 149597870.7
    
    # Оценка угрозы по расстоянию
    if distance_au <= 0.05:  # 0.05 а.е. = ~7.5 млн км (критерий PHA)
        distance_threat = "высокая"
        distance_note = "Расстояние меньше порога потенциально опасных объектов"
    elif distance_au <= 0.1:  # 0.1 а.е. = ~15 млн км
        distance_threat = "средняя"
        distance_note = "Близкое расстояние, требует наблюдения"
    else:
        distance_threat = "низкая"
        distance_note = "Расстояние относительно безопасно"
    
    # Оценка угрозы по размеру
    diameter_m = diameter_km * 1000  # Преобразуем в метры
    
    if diameter_m < 25:
        size_threat = "низкая"
        size_note = "Полное сгорание в атмосфере вероятно"
        impact_category = "локальный" if diameter_m > 10 else "незначительный"
    elif diameter_m < 50:
        size_threat = "средняя"
        size_note = "Воздушный взрыв, возможны фрагменты на поверхности"
        impact_category = "региональный"
    elif diameter_m < 140:
        size_threat = "высокая"
        size_note = "Частичное разрушение, крупные фрагменты достигнут поверхности"
        impact_category = "региональный"
    else:
        size_threat = "критическая"
        size_note = "Катастрофическое воздействие, глобальные последствия"
        impact_category = "глобальный"
    
    # Оценка угрозы по скорости (дополнительный фактор)
    if velocity_km_s > 20:
        velocity_threat = "высокая"
        velocity_note = "Очень высокая скорость, увеличивает энергию воздействия"
    elif velocity_km_s > 15:
        velocity_threat = "средняя"
        velocity_note = "Высокая скорость"
    else:
        velocity_threat = "низкая"
        velocity_note = "Скорость в пределах средних значений"
    
    # Комплексная оценка угрозы
    threat_weights = {
        "низкая": 1,
        "средняя": 2,
        "высокая": 3,
        "критическая": 4
    }
    
    total_threat_score = (
        threat_weights[distance_threat] * 0.4 +  # Вес расстояния: 40%
        threat_weights[size_threat] * 0.5 +      # Вес размера: 50%
        threat_weights[velocity_threat] * 0.1    # Вес скорости: 10%
    )
    
    # Определение итогового уровня угрозы
    if total_threat_score >= 3.5:
        overall_threat = "высокая вероятность падения и катастрофических последствий"
        threat_level = "высокая"
    elif total_threat_score >= 2.5:
        overall_threat = "средняя вероятность падения или значительных разрушений"
        threat_level = "средняя"
    else:
        overall_threat = "низкая вероятность падения или незначительные последствия"
        threat_level = "низкая"
    
    # Расчет кинетической энергии (примерный)
    # Плотность астероида предполагаем 2000 кг/м³ (типично для каменных астероидов)
    density = 2000  # кг/м³
    radius = diameter_m / 2
    volume = (4/3) * math.pi * (radius ** 3)
    mass_kg = volume * density
    energy_joules = 0.5 * mass_kg * (velocity_km_s * 1000) ** 2
    
    # Перевод в мегатонны тротилового эквивалента (1 мегатонна = 4.184e15 Дж)
    energy_megatons = energy_joules / 4.184e15
    
    # Оценка ущерба на основе энергии и категории
    if energy_megatons < 1:
        damage_assessment = "Незначительный ущерб (сгорание в атмосфере)"
    elif energy_megatons < 10:
        damage_assessment = "Локальный ущерб (ударная волна, возможны фрагменты)"
    elif energy_megatons < 100:
        damage_assessment = "Региональный ущерб (разрушения в радиусе десятков км)"
    elif energy_megatons < 1000:
        damage_assessment = "Континентальный ущерб (крупномасштабные разрушения)"
    else:
        damage_assessment = "Глобальный ущерб (климатические изменения, массовые вымирания)"
    
    # Формирование результата
    result = {
        "входные данные": {
            "диаметр(км)": round(diameter_km, 3),
            "расстояние(ае)": round(distance_au, 4),
            "расстояние(км)": round(distance_km, 0),
            "скорость(км/с)": round(velocity_km_s, 1)
        },
        "анализ параметров": {
            "опасность по расстоянию": distance_threat,
            "пояснение расстояния": distance_note,
            "опасность по размеру": size_threat,
            "пояснение размера": size_note,
            "опасность по скорости": velocity_threat,
            "пояснение скорости": velocity_note,
            "категория воздействия": impact_category
        },
        "энергетическая оценка": {
            "кинетическая энергия дж": f"{energy_joules:.2e}",
            "эквивалент мегатонн": round(energy_megatons, 1)
        },
        "итоговая оценка": {
            "степень угрозы": threat_level,
            "вероятность и последствия": overall_threat,
            "оценка ущерба при падении": damage_assessment
        }
    }
    
    return result

