"""
Тесты для получения данных из внешних источников.
"""
import pytest
from unittest.mock import patch, MagicMock
import logging
from api_wrappers.sbdb_api import get_neo

class TestGetData:
    """Тесты для получения данных."""
    
    @pytest.mark.external_api
    @pytest.mark.slow
    def test_get_neo_real_request(self):
        """Реальный запрос к внешнему API.
        
        Этот тест может быть медленным и требует интернет-соединения.
        """
        # Действие
        result = get_neo()
        
        # Проверка
        assert isinstance(result, list)
        
        # Проверяем структуру данных, если есть результаты
        if result:
            first_item = result[0]
            assert "mpc_number" in first_item
            assert "perihelion_au" in first_item
            assert "is_pha" in first_item
            assert "absolute_magnitude" in first_item
            assert "estimated_diameter_km" in first_item
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    def test_get_neo_with_asteroid_having_diameter(self, mock_sbdb, mock_mpc):
        """Обработка астероида с известным диаметром."""
        # Арранжировка моков
        mock_asteroid = {
            'number': 433,
            'name': 'Eros',
            'designation': '1898 DQ',
            'perihelion_distance': 1.13,
            'aphelion_distance': 1.78,
            'earth_moid': 0.15,
            'absolute_magnitude': 10.4,
            'pha': False
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid]
        
        # Мок SBDB
        mock_phys_data = {
            'physical_parameters': {
                'albedo': 0.25,
                'diameter': 16.84
            }
        }
        mock_sbdb.query.return_value = mock_phys_data
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert len(result) == 1
        asteroid_data = result[0]
        assert asteroid_data["mpc_number"] == 433
        assert asteroid_data["name"] == "Eros"
        assert asteroid_data["estimated_diameter_km"] == 16.84
        assert asteroid_data["accurate_diameter"] == True
        assert asteroid_data["albedo"] == 0.25
        assert asteroid_data["is_pha"] == False
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    @patch('utils.get_data.get_size_by_h_mag')
    def test_get_neo_with_asteroid_without_diameter(self, mock_size_func, mock_sbdb, mock_mpc):
        """Обработка астероида без диаметра (расчет)."""
        # Арранжировка
        # Создаем словарь с данными вместо MagicMock
        mock_asteroid_data = {
            'number': 99942,
            'name': 'Apophis',
            'designation': None,
            'perihelion_distance': 0.75,
            'aphelion_distance': 1.1,
            'earth_moid': 0.0002,
            'absolute_magnitude': 19.7,
            'pha': 'Y'
        }
        
        # Используем обычный словарь для теста
        mock_mpc.query_objects.return_value = [mock_asteroid_data]
        mock_sbdb.query.return_value = {}  # Нет физических данных
        
        # Мок функции расчета размера
        mock_size_func.return_value = 0.3
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert len(result) == 1
        assert result[0]["accurate_diameter"] == False
        assert result[0]["estimated_diameter_km"] == 0.3
        assert result[0]["albedo"] == 0.15  # Стандартное значение
        assert result[0]["is_pha"] == True  # 'Y' должно преобразоваться в True
        mock_size_func.assert_called_once_with(19.7)
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    @patch('utils.get_data.get_size_by_albedo')
    def test_get_neo_with_asteroid_with_albedo(self, mock_size_func, mock_sbdb, mock_mpc):
        """Обработка астероида с известным альбедо."""
        # Арранжировка
        # Создаем словарь вместо MagicMock
        mock_asteroid = {
            'number': 12345,
            'perihelion_distance': 0.9,
            'aphelion_distance': 1.5,
            'earth_moid': 0.08,
            'absolute_magnitude': 20.0,
            'pha': False
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid]
        
        # Мок SBDB с альбедо но без диаметра
        mock_phys_data = {
            'physical_parameters': {
                'albedo': 0.3,
                'diameter': None
            }
        }
        mock_sbdb.query.return_value = mock_phys_data
        
        # Мок функции расчета
        mock_size_func.return_value = 0.25
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert result[0]["albedo"] == 0.3
        mock_size_func.assert_called_once_with(0.3, 20.0)
    
    @patch('utils.get_data.MPC')
    def test_get_neo_handles_mpc_exception(self, mock_mpc):
        """Обработка исключений MPC."""
        # Арранжировка
        mock_mpc.query_objects.side_effect = Exception("MPC API error")
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert result == []
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    def test_get_neo_handles_sbdb_exception(self, mock_sbdb, mock_mpc):
        """Обработка исключений SBDB."""
        # Арранжировка
        # Используем обычный словарь
        mock_asteroid = {
            'number': 99999,
            'perihelion_distance': 0.8,
            'aphelion_distance': 1.4,
            'earth_moid': 0.06,
            'absolute_magnitude': 21.0,
            'pha': True
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid]
        mock_sbdb.query.side_effect = Exception("SBDB API error")
        
        # Действие
        result = get_neo()
        
        # Проверка
        # Должен обработать исключение и продолжить
        assert len(result) == 1
        # Должен использовать стандартное альбедо
        assert result[0]["albedo"] == 0.15
    
    @patch('utils.get_data.MPC')
    def test_get_neo_filters_by_perihelion(self, mock_mpc):
        """Фильтрация по перигелию (≤ 1.3 а.е.)."""
        # Арранжировка
        # Используем обычные словари
        mock_neo = {
            'number': 1,
            'perihelion_distance': 0.9,  # NEO
            'aphelion_distance': 1.8,
            'earth_moid': 0.05,
            'absolute_magnitude': 20.0,
            'pha': False
        }
        
        mock_non_neo = {
            'number': 2,
            'perihelion_distance': 2.0,  # Не NEO
            'aphelion_distance': 3.0,
            'earth_moid': 0.5,
            'absolute_magnitude': 18.0,
            'pha': False
        }
        
        mock_mpc.query_objects.return_value = [mock_neo, mock_non_neo]
        
        # Действие
        result = get_neo()
        
        # Проверка
        # Должен отфильтровать только NEO (перигелий ≤ 1.3)
        assert len(result) == 1
        assert result[0]["mpc_number"] == 1
    
    def test_get_neo_logging(self, caplog):
        """Проверка логирования."""
        with patch('utils.get_data.MPC') as mock_mpc:
            # Используем обычный словарь
            mock_asteroid = {
                'number': 999,
                'name': 'Test',
                'perihelion_distance': 1.0,
                'aphelion_distance': 1.8,
                'earth_moid': 0.1,
                'absolute_magnitude': 20.0,
                'pha': False
            }
            
            mock_mpc.query_objects.return_value = [mock_asteroid]
            
            with caplog.at_level(logging.INFO):
                get_neo()
            
            # Проверяем, что было логирование
            assert "Данные для астероида" in caplog.text
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    def test_get_neo_with_missing_optional_fields(self, mock_sbdb, mock_mpc):
        """Обработка астероида с отсутствующими необязательными полями."""
        # Арранжировка
        # Используем обычный словарь
        mock_asteroid = {
            'number': 77777,
            'name': None,  # Отсутствующее имя
            'perihelion_distance': 1.0,
            'aphelion_distance': 1.7,
            'earth_moid': 0.07,
            'absolute_magnitude': 21.5,
            'pha': 'Y'
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid]
        mock_sbdb.query.return_value = {}
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert len(result) == 1
        # Имя должно быть заменено на Unknown_номер
        assert result[0]["name"] == "Unknown_77777"
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    @patch('utils.get_data.get_size_by_albedo')
    def test_get_neo_with_invalid_albedo(self, mock_size_func, mock_sbdb, mock_mpc):
        """Обработка некорректного альбедо из SBDB."""
        # Арранжировка
        # Используем обычный словарь
        mock_asteroid = {
            'number': 88888,
            'perihelion_distance': 0.95,
            'aphelion_distance': 1.6,
            'earth_moid': 0.09,
            'absolute_magnitude': 22.0,
            'pha': False
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid]
        
        # Мок SBDB с некорректным альбедо
        mock_phys_data = {
            'physical_parameters': {
                'albedo': -0.1,  # Некорректное альбедо
                'diameter': None
            }
        }
        mock_sbdb.query.return_value = mock_phys_data
        
        # Мок функции расчета
        mock_size_func.return_value = 0.15
        
        # Действие
        result = get_neo()
        
        # Проверка
        # Должен использовать стандартное альбедо при некорректном
        assert result[0]["albedo"] == 0.15
    
    def test_get_neo_empty_result(self):
        """Обработка пустого результата от MPC."""
        with patch('utils.get_data.MPC') as mock_mpc:
            mock_mpc.query_objects.return_value = []
            
            result = get_neo()
            assert result == []
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    def test_get_neo_with_asteroid_having_phadata(self, mock_sbdb, mock_mpc):
        """Обработка астероида с флагом PHA."""
        # Арранжировка
        # Используем обычный словарь
        mock_asteroid = {
            'number': 123456,
            'name': 'PHA Test',
            'perihelion_distance': 0.85,
            'aphelion_distance': 1.6,
            'earth_moid': 0.02,
            'absolute_magnitude': 18.5,
            'pha': 'Y'  # Флаг PHA - строка 'Y'
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid]
        mock_sbdb.query.return_value = {}
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert len(result) == 1
        # Флаг PHA должен быть преобразован в bool
        assert result[0]["is_pha"] == True
    
    def test_get_neo_data_structure(self):
        """Проверка структуры возвращаемых данных."""
        with patch('utils.get_data.MPC') as mock_mpc, \
             patch('utils.get_data.SBDB') as mock_sbdb:
            
            # Используем обычный словарь
            mock_asteroid = {
                'number': 111111,
                'name': 'Struct Test',
                'designation': '2024 AB1',
                'perihelion_distance': 1.0,
                'aphelion_distance': 1.9,
                'earth_moid': 0.08,
                'absolute_magnitude': 19.0,
                'pha': False
            }
            
            mock_mpc.query_objects.return_value = [mock_asteroid]
            mock_sbdb.query.return_value = {}
            
            result = get_neo()
            
            # Проверяем все поля
            asteroid_data = result[0]
            expected_fields = [
                "mpc_number",
                "name",
                "designation",
                "perihelion_au",
                "aphelion_au",
                "earth_moid_au",
                "is_neo",
                "is_pha",
                "absolute_magnitude",
                "estimated_diameter_km",
                "accurate_diameter",
                "albedo"
            ]
            
            for field in expected_fields:
                assert field in asteroid_data
    
    @patch('utils.get_data.MPC')
    @patch('utils.get_data.SBDB')
    def test_get_neo_multiple_asteroids(self, mock_sbdb, mock_mpc):
        """Обработка нескольких астероидов."""
        # Арранжировка
        # Используем обычные словари
        mock_asteroid1 = {
            'number': 100001,
            'name': 'Asteroid 1',
            'perihelion_distance': 0.9,
            'aphelion_distance': 1.8,
            'earth_moid': 0.05,
            'absolute_magnitude': 20.0,
            'pha': False
        }
        
        mock_asteroid2 = {
            'number': 100002,
            'name': 'Asteroid 2',
            'perihelion_distance': 1.1,
            'aphelion_distance': 2.0,
            'earth_moid': 0.1,
            'absolute_magnitude': 21.0,
            'pha': True
        }
        
        mock_mpc.query_objects.return_value = [mock_asteroid1, mock_asteroid2]
        mock_sbdb.query.return_value = {}
        
        # Действие
        result = get_neo()
        
        # Проверка
        assert len(result) == 2
        assert result[0]["mpc_number"] == 100001
        assert result[1]["mpc_number"] == 100002
        assert result[0]["is_pha"] == False
        assert result[1]["is_pha"] == True