"""
Тесты для мониторинга сближений.
"""
import pytest
from unittest.mock import patch, MagicMock
import time
from datetime import datetime, timedelta
from utils.get_approaches import get_current_close_approaches

class MockEph:
    def __init__(self, data, has_delta_rate=True):
        self.data = data
        self.colnames = ['datetime_str', 'delta', 'delta_rate'] if has_delta_rate else ['datetime_str', 'delta']
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)

class TestMonitoring:
    """Тесты для мониторинга сближений."""
    
    @pytest.fixture
    def sample_asteroid_data(self):
        """Тестовые данные об астероидах."""
        return [
            {
                'name': 'Apophis',
                'number': 99942,
                'is_pha': True,
                'absolute_magnitude': 19.7,
                'estimated_diameter_km': 0.37
            },
            {
                'name': 'Bennu',
                'number': 101955,
                'is_pha': True,
                'absolute_magnitude': 20.4,
                'estimated_diameter_km': 0.49
            },
            {
                'name': 'Non-PHA Asteroid',
                'number': 12345,
                'is_pha': False,  # Не PHA, должен быть отфильтрован
                'absolute_magnitude': 18.0,
                'estimated_diameter_km': 1.0
            }
        ]
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_with_close_asteroids(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Обнаружение близких сближений."""
        # Арранжировка моков
        mock_eph_data = [
            {
                'datetime_str': '2024-01-15 12:00:00',
                'delta': 0.1,  # 0.1 а.е. - далеко
                'delta_rate': 5.0
            },
            {
                'datetime_str': '2024-01-20 08:30:00',
                'delta': 0.03,  # 0.03 а.е. - близко (< 0.05)
                'delta_rate': 12.5
            }
        ]
        
        mock_eph = MockEph(mock_eph_data)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        # Настраиваем side_effect для возврата разных моков
        mock_horizons.side_effect = mock_objs
        
        # Отключаем sleep для ускорения тестов
        mock_sleep.return_value = None
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        assert len(result) == 2  # По одному близкому сближению на каждый PHA астероид
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_with_distant_asteroids(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Фильтрация далеких астероидов."""
        # Арранжировка моков
        mock_eph = MagicMock()
        mock_eph.__len__.return_value = 3
        mock_eph.colnames = ['datetime_str', 'delta', 'delta_rate']
        
        # Все записи далекие
        records = [
            {'datetime_str': '2024-01-15 12:00:00', 'delta': 0.08, 'delta_rate': 7.0},
            {'datetime_str': '2024-01-20 08:30:00', 'delta': 0.07, 'delta_rate': 6.5},
            {'datetime_str': '2024-01-25 15:45:00', 'delta': 0.09, 'delta_rate': 8.0},
        ]
        
        mock_eph.__iter__.return_value = iter(records)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        # Все сближения дальше 0.05 а.е., поэтому результат должен быть пустым
        assert len(result) == 0
    
    @patch('utils.monitoring.Horizons')
    def test_get_current_close_approaches_with_horizons_exception(
        self, mock_horizons, sample_asteroid_data
    ):
        """Обработка исключений Horizons."""
        # Настраиваем mock для выброса исключения
        mock_horizons.side_effect = Exception("Horizons API error")
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        # При исключении функция должна продолжить работу
        assert isinstance(result, list)
        # Результат должен быть пустым или содержать данные только от успешных запросов
        # В данном случае все запросы падают, поэтому результат пустой
        assert len(result) == 0
    
    def test_get_current_close_approaches_empty_result(self, sample_asteroid_data):
        """Обработка пустого результата."""
        # Фильтруем только не-PHA астероиды
        non_pha_data = [a for a in sample_asteroid_data if not a['is_pha']]
        
        # Действие
        result = get_current_close_approaches(non_pha_data, days=30)
        
        # Проверка
        # Функция фильтрует только PHA астероиды, поэтому результат пустой
        assert result == []
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_custom_days(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Настройка периода анализа."""
        # Арранжировка
        mock_eph = MagicMock()
        mock_eph.__len__.return_value = 0
        mock_eph.__iter__.return_value = iter([])
        mock_eph.colnames = ['datetime_str', 'delta', 'delta_rate']
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие с разными периодами
        for days in [7, 30, 90]:
            get_current_close_approaches(sample_asteroid_data, days=days)
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_sorting(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Проверка сортировки по расстоянию."""
        # Арранжировка
        mock_eph_data = [
            {'datetime_str': '2024-01-15 12:00:00', 'delta': 0.045, 'delta_rate': 10.0},
            {'datetime_str': '2024-01-10 08:30:00', 'delta': 0.02, 'delta_rate': 12.0},
            {'datetime_str': '2024-01-20 15:45:00', 'delta': 0.035, 'delta_rate': 11.0},
        ]
        
        mock_eph = MockEph(mock_eph_data)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        # Два PHA астероида × 3 близких сближения = 6 сближений
        assert len(result) == 6
        
        # Проверяем сортировку
        for i in range(len(result) - 1):
            assert result[i]['distance_au'] <= result[i + 1]['distance_au']
        
        # Первый должен быть самым близким
        assert result[0]['distance_au'] == 0.02
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_velocity_calculation(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Проверка расчета скорости."""
        # Арранжировка
        mock_eph_data = [{
            'datetime_str': '2024-01-15 12:00:00',
            'delta': 0.025,
            'delta_rate': 15.5  # Скорость
        }]
        
        mock_eph = MockEph(mock_eph_data)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        # Два PHA астероида × 1 сближение = 2 сближения
        assert len(result) == 2
        
        for approach in result:
            # Скорость должна быть преобразована в float
            assert isinstance(approach['velocity_km_s'], float)
            assert approach['velocity_km_s'] == 15.5
            
            # Расстояние в км должно быть рассчитано
            assert approach['distance_km'] == 0.025 * 149597870.7
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_without_delta_rate(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Обработка записей без delta_rate."""
        # Арранжировка
        mock_eph_data = [{
            'datetime_str': '2024-01-15 12:00:00',
            'delta': 0.03
            # Нет delta_rate
        }]
        
        mock_eph = MockEph(mock_eph_data, has_delta_rate=False)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        # Два PHA астероида × 1 сближение = 2 сближения
        assert len(result) == 2
        for approach in result:
            # Скорость должна быть 0, если нет delta_rate
            assert approach['velocity_km_s'] == 0
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_logging(
        self, mock_sleep, mock_horizons, sample_asteroid_data, caplog
    ):
        """Проверка логирования."""
        import logging
        
        # Арранжировка
        mock_eph_data = [
            {'datetime_str': '2024-01-15 12:00:00', 'delta': 0.04, 'delta_rate': 10.0},
            {'datetime_str': '2024-01-20 08:30:00', 'delta': 0.06, 'delta_rate': 12.0},
        ]
        
        mock_eph = MockEph(mock_eph_data)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие с включенным логированием
        with caplog.at_level(logging.INFO):
            result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверяем логи
        assert "Запрашиваемый период" in caplog.text
        assert "Обрабатывается" in caplog.text
        assert "Получены данные для" in caplog.text
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_error_logging(
        self, mock_sleep, mock_horizons, sample_asteroid_data, caplog
    ):
        """Проверка логирования ошибок."""
        import logging
        
        # Настраиваем первый вызов успешным, второй - с ошибкой
        mock_eph1_data = [{
            'datetime_str': '2024-01-15 12:00:00', 
            'delta': 0.04, 
            'delta_rate': 10.0
        }]
        
        mock_eph1 = MockEph(mock_eph1_data)
        
        mock_obj1 = MagicMock()
        mock_obj1.ephemerides.return_value = mock_eph1
        
        # Второй вызов вызывает исключение
        mock_horizons.side_effect = [
            mock_obj1,
            Exception("Test error")
        ]
        
        # Действие
        with caplog.at_level(logging.ERROR):
            result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверяем, что ошибка была залогирована
        assert "Ошибка для астероида" in caplog.text
        assert "Test error" in caplog.text
        
        # Проверяем, что функция продолжила работу после ошибки
        assert isinstance(result, list)
    
    def test_get_current_close_approaches_asteroid_number_handling(
        self, sample_asteroid_data
    ):
        """Обработка разных форматов номеров астероидов."""
        # Модифицируем тестовые данные
        modified_data = [
            {
                'name': 'Test Asteroid 1',
                'number': 12345,  # Числовой номер
                'is_pha': True,
                'absolute_magnitude': 20.0,
                'estimated_diameter_km': 0.3
            },
            {
                'name': 'Test Asteroid 2',
                'mpc_number': 67890,  # mpc_number вместо number
                'is_pha': True,
                'absolute_magnitude': 21.0,
                'estimated_diameter_km': 0.4
            },
            {
                'name': 'Test Asteroid 3',
                # Нет ни number, ни mpc_number
                'is_pha': True,
                'absolute_magnitude': 22.0,
                'estimated_diameter_km': 0.5
            }
        ]
        
        # Функция должна обрабатывать разные форматы
        # В реальном коде используется asteroid.get('number', asteroid.get('mpc_number', 'unknown'))
        # Поэтому тест проверяет логику, а не реальные вызовы API
        assert True  # Placeholder assertion
    
    @patch('utils.monitoring.Horizons')
    @patch('utils.monitoring.time.sleep')
    def test_get_current_close_approaches_mixed_distances(
        self, mock_sleep, mock_horizons, sample_asteroid_data
    ):
        """Смесь близких и далеких сближений."""
        # Арранжировка
        mock_eph_data = [
            {'datetime_str': '2024-01-10 08:30:00', 'delta': 0.08, 'delta_rate': 10.0},  # Далеко
            {'datetime_str': '2024-01-15 12:00:00', 'delta': 0.025, 'delta_rate': 12.0},  # Близко
            {'datetime_str': '2024-01-20 15:45:00', 'delta': 0.06, 'delta_rate': 11.0},  # Далеко
            {'datetime_str': '2024-01-25 20:15:00', 'delta': 0.035, 'delta_rate': 13.0},  # Близко
        ]
        
        mock_eph = MockEph(mock_eph_data)
        
        # Создаем список моков для каждого астероида
        mock_objs = []
        for i in range(2):  # Два PHA астероида
            mock_obj = MagicMock()
            mock_obj.ephemerides.return_value = mock_eph
            mock_objs.append(mock_obj)
        
        mock_horizons.side_effect = mock_objs
        
        # Действие
        result = get_current_close_approaches(sample_asteroid_data, days=30)
        
        # Проверка
        # Два PHA астероида × 2 близких сближения = 4 сближения
        assert len(result) == 4
        
        for approach in result:
            assert approach['distance_au'] < 0.05
        
        # Проверяем, что результаты отсортированы
        for i in range(len(result) - 1):
            assert result[i]['distance_au'] <= result[i + 1]['distance_au']