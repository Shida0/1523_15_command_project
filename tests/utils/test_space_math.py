"""
Тесты для математических расчетов.
"""
import pytest
import math
from utils.space_math import (
    get_size_by_albedo,
    get_size_by_h_mag,
    count_danger
)

class TestSpaceMath:
    """Тесты математических функций."""
    
    def test_get_size_by_albedo_with_valid_input(self):
        """Расчет диаметра по альбедо и абсолютной величине."""
        # Арранжировка
        albedo = 0.25
        h_mag = 18.5
        
        # Действие
        diameter = get_size_by_albedo(albedo, h_mag)
        
        # Проверка
        expected = 1329 / (albedo ** 0.5) * (10 ** (-0.2 * h_mag))
        assert diameter == expected
        assert diameter > 0
    
    def test_get_size_by_albedo_with_zero_albedo(self):
        """Обработка нулевого альбедо."""
        # Теперь функция выбрасывает ValueError
        with pytest.raises(ValueError, match="Альбедо должно быть положительным числом"):
            get_size_by_albedo(0, 18.5)
    
    def test_get_size_by_albedo_with_negative_albedo(self):
        """Обработка отрицательного альбедо (корень из отрицательного)."""
        # Корень из отрицательного числа вызовет ValueError
        with pytest.raises(ValueError):
            get_size_by_albedo(-0.1, 18.5)
    
    def test_get_size_by_h_mag_with_valid_input(self):
        """Расчет диаметра по стандартному альбедо."""
        # Арранжировка
        h_mag = 18.5
        
        # Действие
        diameter = get_size_by_h_mag(h_mag)
        
        # Проверка
        expected = 1329 / (0.15 ** 0.5) * (10 ** (-0.2 * h_mag))
        assert diameter == expected
    
    def test_get_size_by_h_mag_with_extreme_values(self):
        """Расчет с экстремальными значениями H-магнитуды."""
        # Тестируем разные значения H
        test_cases = [
            (10, 1329 / (0.15 ** 0.5) * (10 ** (-0.2 * 10))),
            (20, 1329 / (0.15 ** 0.5) * (10 ** (-0.2 * 20))),
            (30, 1329 / (0.15 ** 0.5) * (10 ** (-0.2 * 30))),
        ]
        
        for h_mag, expected in test_cases:
            result = get_size_by_h_mag(h_mag)
            assert result == expected
    
    def test_count_danger_with_small_asteroid(self):
        """Оценка опасности для малого астероида."""
        # Арранжировка
        diameter_km = 0.03  # 30 метров
        distance_au = 0.1   # 15 млн км
        velocity_km_s = 15  # 15 км/с
        
        # Действие
        result = count_danger(diameter_km, distance_au, velocity_km_s)
        
        # Проверка
        assert isinstance(result, dict)
        assert "входные данные" in result
        assert "анализ параметров" in result
        assert "энергетическая оценка" in result
        assert "итоговая оценка" in result
        
        # Проверяем структуру результата
        assert "диаметр(км)" in result["входные данные"]
        assert "расстояние(ае)" in result["входные данные"]
        assert "расстояние(км)" in result["входные данные"]
        assert "скорость(км/с)" in result["входные данные"]
        
        assert "опасность по расстоянию" in result["анализ параметров"]
        assert "опасность по размеру" in result["анализ параметров"]
        assert "опасность по скорости" in result["анализ параметров"]
        assert "категория воздействия" in result["анализ параметров"]
        
        assert "степень угрозы" in result["итоговая оценка"]
        
        # Для малого астероида должна быть низкая или средняя опасность
        assert result["итоговая оценка"]["степень угрозы"] in ["низкая", "средняя"]
    
    def test_count_danger_with_large_asteroid(self):
        """Оценка опасности для крупного астероида."""
        # Арранжировка
        diameter_km = 5.0  # 5 км
        distance_au = 0.05  # 7.5 млн км
        velocity_km_s = 20  # 20 км/с
        
        # Действие
        result = count_danger(diameter_km, distance_au, velocity_km_s)
        
        # Проверка
        # Крупный астероид должен иметь высокую или критическую опасность
        assert result["итоговая оценка"]["степень угрозы"] in ["высокая", "критическая"]
        assert float(result["энергетическая оценка"]["эквивалент мегатонн"]) > 0
    
    def test_count_danger_with_close_approach(self):
        """Оценка опасности при близком сближении."""
        # Арранжировка
        diameter_km = 0.1  # 100 метров
        distance_au = 0.02  # 3 млн км (близко!)
        velocity_km_s = 18
        
        # Действие
        result = count_danger(diameter_km, distance_au, velocity_km_s)
        
        # Проверка
        # При близком сближении должна быть высокая опасность по расстоянию
        assert result["анализ параметров"]["опасность по расстоянию"] == "высокая"
    
    def test_count_danger_with_far_approach(self):
        """Оценка опасности при далеком сближении."""
        # Арранжировка
        diameter_km = 0.5  # 500 метров
        distance_au = 0.5  # 75 млн км (далеко)
        velocity_km_s = 15
        
        # Действие
        result = count_danger(diameter_km, distance_au, velocity_km_s)
        
        # Проверка
        # При далеком сближении должна быть низкая опасность по расстоянию
        assert result["анализ параметров"]["опасность по расстоянию"] == "низкая"
    
    def test_count_danger_with_high_velocity(self):
        """Оценка опасности при высокой скорости."""
        # Арранжировка
        diameter_km = 0.1
        distance_au = 0.1
        velocity_km_s = 30  # Очень высокая скорость
        
        # Действие
        result = count_danger(diameter_km, distance_au, velocity_km_s)
        
        # Проверка
        # При высокой скорости должна быть высокая опасность по скорости
        assert result["анализ параметров"]["опасность по скорости"] == "высокая"
    
    def test_count_danger_edge_cases(self):
        """Граничные случаи."""
        # Тест 1: Нулевой диаметр
        result = count_danger(0, 0.1, 15)
        assert result["анализ параметров"]["опасность по размеру"] == "низкая"
        assert result["анализ параметров"]["категория воздействия"] == "незначительный"
        
        # Тест 2: Нулевое расстояние
        result = count_danger(0.1, 0, 15)
        assert result["анализ параметров"]["опасность по расстоянию"] == "высокая"
        
        # Тест 3: Нулевая скорость
        result = count_danger(0.1, 0.1, 0)
        assert result["анализ параметров"]["опасность по скорости"] == "низкая"
        assert float(result["энергетическая оценка"]["эквивалент мегатонн"]) == 0
    
    def test_count_danger_negative_values(self):
        """Обработка отрицательных значений."""
        # Отрицательные значения должны обрабатываться, но давать странные результаты
        result = count_danger(-0.1, -0.1, -15)
        
        # Проверяем, что функция не падает и возвращает результат
        assert isinstance(result, dict)
        assert "энергетическая оценка" in result
        
        # Энергия должна быть положительной (масса всегда положительна)
        energy = float(result["энергетическая оценка"]["эквивалент мегатонн"])
        assert energy >= 0
    
    @pytest.mark.parametrize("diameter,expected_category", [
        (0.001, "незначительный"),   # 1 метр
        (0.015, "локальный"),        # 15 метров
        (0.025, "локальный"),        # 25 метров
        (0.035, "региональный"),     # 35 метров
        (0.1, "региональный"),       # 100 метров
        (0.12, "региональный"),      # 120 метров
        (0.15, "глобальный"),        # 150 метров
        (1.0, "глобальный"),         # 1 км
    ])
    def test_count_danger_size_categories(self, diameter, expected_category):
        """Проверка категорий воздействия в зависимости от размера."""
        result = count_danger(diameter, 0.1, 15)
        assert result["анализ параметров"]["категория воздействия"] == expected_category
    
    def test_count_danger_energy_calculation(self):
        """Проверка расчета энергии."""
        # Арранжировка
        diameter_km = 0.1  # 100 метров = 100,000 мм
        velocity_km_s = 10
        
        # Расчет вручную для проверки
        diameter_m = diameter_km * 1000  # 100 метров
        radius = diameter_m / 2  # 50 метров
        volume = (4/3) * math.pi * (radius ** 3)  # объем сферы
        density = 2000  # кг/м³
        mass_kg = volume * density
        energy_joules = 0.5 * mass_kg * (velocity_km_s * 1000) ** 2
        expected_energy_mt = energy_joules / 4.184e15
        
        # Действие
        result = count_danger(diameter_km, 0.1, velocity_km_s)
        
        # Проверка
        actual_energy = float(result["энергетическая оценка"]["эквивалент мегатонн"])
        # Допускаем погрешность из-за округления
        assert abs(actual_energy - expected_energy_mt) < 0.1
    
    def test_count_danger_output_format(self):
        """Проверка формата выходных данных."""
        result = count_danger(0.1, 0.1, 15)
        
        # Проверяем типы данных
        assert isinstance(result["входные данные"]["диаметр(км)"], float)
        assert isinstance(result["входные данные"]["расстояние(ае)"], float)
        assert isinstance(result["входные данные"]["расстояние(км)"], float)
        assert isinstance(result["входные данные"]["скорость(км/с)"], float)
        
        assert isinstance(result["анализ параметров"]["опасность по расстоянию"], str)
        assert isinstance(result["анализ параметров"]["пояснение расстояния"], str)
        assert isinstance(result["анализ параметров"]["опасность по размеру"], str)
        assert isinstance(result["анализ параметров"]["пояснение размера"], str)
        assert isinstance(result["анализ параметров"]["опасность по скорости"], str)
        assert isinstance(result["анализ параметров"]["пояснение скорости"], str)
        assert isinstance(result["анализ параметров"]["категория воздействия"], str)
        
        assert isinstance(result["энергетическая оценка"]["кинетическая энергия дж"], str)
        assert isinstance(result["энергетическая оценка"]["эквивалент мегатонн"], float)
        
        assert isinstance(result["итоговая оценка"]["степень угрозы"], str)
        assert isinstance(result["итоговая оценка"]["вероятность и последствия"], str)
        assert isinstance(result["итоговая оценка"]["оценка ущерба при падении"], str)
    
    def test_count_danger_threshold_distances(self):
        """Проверка пороговых значений расстояния."""
        # Тест 1: чуть меньше 0.05 а.е.
        result1 = count_danger(0.1, 0.049, 15)
        assert result1["анализ параметров"]["опасность по расстоянию"] == "высокая"
        
        # Тест 2: ровно 0.05 а.е.
        result2 = count_danger(0.1, 0.05, 15)
        assert result2["анализ параметров"]["опасность по расстоянию"] == "высокая"
        
        # Тест 3: чуть больше 0.05 а.е.
        result3 = count_danger(0.1, 0.051, 15)
        assert result3["анализ параметров"]["опасность по расстоянию"] == "средняя"
        
        # Тест 4: 0.1 а.е.
        result4 = count_danger(0.1, 0.1, 15)
        assert result4["анализ параметров"]["опасность по расстоянию"] == "средняя"
        
        # Тест 5: больше 0.1 а.е.
        result5 = count_danger(0.1, 0.11, 15)
        assert result5["анализ параметров"]["опасность по расстоянию"] == "низкая"
    
    def test_count_danger_threshold_velocities(self):
        """Проверка пороговых значений скорости."""
        # Тест 1: 15 км/с (граница)
        result1 = count_danger(0.1, 0.1, 15)
        assert result1["анализ параметров"]["опасность по скорости"] == "средняя"
        
        # Тест 2: 16 км/с (чуть выше границы)
        result2 = count_danger(0.1, 0.1, 16)
        assert result2["анализ параметров"]["опасность по скорости"] == "средняя"
        
        # Тест 3: 20 км/с (граница высокой)
        result3 = count_danger(0.1, 0.1, 20)
        assert result3["анализ параметров"]["опасность по скорости"] == "высокая"
        
        # Тест 4: 25 км/с (высокая)
        result4 = count_danger(0.1, 0.1, 25)
        assert result4["анализ параметров"]["опасность по скорости"] == "высокая"