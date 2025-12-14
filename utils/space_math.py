import math

def get_size_by_albedo(albedo: float, h_mag: float) -> float:
    """Вычисляет диаметр астероида на основе альбедо и абсолютной звёздной величины."""
    if albedo <= 0:
        raise ValueError(f"Альбедо должно быть положительным числом. Получено: {albedo}")
    return 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))

def get_size_by_h_mag(h_mag: float) -> float:
    """Вычисляет диаметр астероида с использованием стандартного альбедо."""
    assumed_albedo = 0.15
    return get_size_by_albedo(assumed_albedo, h_mag)

def count_danger(diameter_km, distance_au, velocity_km_s):
    """
    Оценивает опасность астероида на основе диаметра, расстояния до Земли и скорости.
    """
    
    distance_km_value = distance_au * 149597870.7
    
    # Оценка угрозы по расстоянию
    if distance_au <= 0.05:
        distance_threat = "высокая"
        distance_note = "Расстояние меньше порога потенциально опасных объектов"
    elif distance_au <= 0.1:
        distance_threat = "средняя"
        distance_note = "Близкое расстояние, требует наблюдения"
    else:
        distance_threat = "низкая"
        distance_note = "Расстояние относительно безопасно"
    
    # Оценка угрозы по размеру
    diameter_m = abs(diameter_km) * 1000
    
    if diameter_m <= 25:
        size_threat = "низкая"
        size_note = "Полное сгорание в атмосфере вероятно"
        impact_category = "локальный" if diameter_m > 10 else "незначительный"
    elif diameter_m <= 50:
        size_threat = "средняя"
        size_note = "Воздушный взрыв, возможны фрагменты на поверхности"
        impact_category = "региональный"
    elif diameter_m <= 140:
        size_threat = "высокая"
        size_note = "Частичное разрушение, крупные фрагменты достигнут поверхности"
        impact_category = "региональный"
    else:
        size_threat = "критическая"
        size_note = "Катастрофическое воздействие, глобальные последствия"
        impact_category = "глобальный"
    
    # Оценка угрозы по скорости (корректные пороги)
    if velocity_km_s >= 20:
        velocity_threat = "высокая"
        velocity_note = "Очень высокая скорость, увеличивает энергию воздействия"
    elif velocity_km_s >= 15:
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
        threat_weights[distance_threat] * 0.4 +
        threat_weights[size_threat] * 0.5 +
        threat_weights[velocity_threat] * 0.1
    )
    
    # Определение итогового уровня угрозы (скорректированные пороги)
    if total_threat_score >= 3.4:  # Было 3.5
        overall_threat = "высокая вероятность падения и катастрофических последствий"
        threat_level = "высокая"
    elif total_threat_score >= 2.4:  # Было 2.5
        overall_threat = "средняя вероятность падения или значительных разрушений"
        threat_level = "средняя"
    else:
        overall_threat = "низкая вероятность падения или незначительные последствия"
        threat_level = "низкая"
    
    # Расчет кинетической энергии
    density = 2000
    radius = abs(diameter_m) / 2
    volume = (4/3) * math.pi * (radius ** 3)
    mass_kg = abs(volume * density)
    energy_joules = 0.5 * mass_kg * (abs(velocity_km_s) * 1000) ** 2
    energy_megatons = energy_joules / 4.184e15
    
    # Оценка ущерба
    if energy_megatons <= 1:
        damage_assessment = "Незначительный ущерб (сгорание в атмосфере)"
    elif energy_megatons <= 10:
        damage_assessment = "Локальный ущерб (ударная волна, возможны фрагменты)"
    elif energy_megatons <= 100:
        damage_assessment = "Региональный ущерб (разрушения в радиусе десятков км)"
    elif energy_megatons <= 1000:
        damage_assessment = "Континентальный ущерб (крупномасштабные разрушения)"
    else:
        damage_assessment = "Глобальный ущерб (климатические изменения, массовые вымирания)"
    
    result = {
        "входные данные": {
            "диаметр(км)": round(diameter_km, 3),
            "расстояние(ае)": round(distance_au, 4),
            "расстояние(км)": round(distance_km_value, 0),
            "скорость(км/с)": float(round(velocity_km_s, 1))
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