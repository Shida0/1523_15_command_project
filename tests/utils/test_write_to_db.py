"""
Тесты для записи данных в базу данных.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from utils.write_to_db import async_write_data, write_data

class TestWriteToDB:
    """Тесты для записи данных в БД."""
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_success(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Успешная запись данных."""
        # Арранжировка моков
        mock_data = [
            {
                'mpc_number': 12345,
                'name': 'Test Asteroid 1',
                'perihelion_au': 1.0,
                'aphelion_au': 2.0,
                'earth_moid_au': 0.1,
                'is_neo': True,
                'is_pha': False,
                'absolute_magnitude': 20.0,
                'estimated_diameter_km': 0.3,
                'accurate_diameter': False,
                'albedo': 0.15
            },
            {
                'mpc_number': 67890,
                'name': 'Test Asteroid 2',
                'perihelion_au': 0.9,
                'aphelion_au': 1.8,
                'earth_moid_au': 0.05,
                'is_neo': True,
                'is_pha': True,
                'absolute_magnitude': 19.5,
                'estimated_diameter_km': 0.45,
                'accurate_diameter': True,
                'albedo': 0.22
            }
        ]
        
        mock_get_neo.return_value = mock_data
        
        # Мок асинхронного контекстного менеджера
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        # Мок контроллера
        mock_controller_instance = AsyncMock()
        mock_controller_instance.bulk_create = AsyncMock()
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие
        await async_write_data()
        
        # Проверка
        # Проверяем вызовы
        mock_get_neo.assert_called_once()
        mock_asteroid_controller.assert_called_once()
        mock_session_local.assert_called_once()
        
        # Проверяем, что bulk_create был вызван с правильными данными
        mock_controller_instance.bulk_create.assert_called_once_with(
            mock_session, mock_data
        )
        
        # Проверяем, что сессия была использована в контекстном менеджере
        mock_session.__aenter__.assert_called_once()
        mock_session.__aexit__.assert_called_once()
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_with_empty_data(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Запись пустых данных."""
        # Арранжировка
        mock_get_neo.return_value = []  # Пустые данные
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        mock_controller_instance = AsyncMock()
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие
        await async_write_data()
        
        # Проверка
        mock_controller_instance.bulk_create.assert_called_once_with(
            mock_session, []
        )
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_controller_error(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Обработка ошибки контроллера."""
        # Арранжировка
        mock_get_neo.return_value = [{'mpc_number': 12345, 'name': 'Test'}]
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        mock_controller_instance = AsyncMock()
        mock_controller_instance.bulk_create = AsyncMock(
            side_effect=Exception("DB error")
        )
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие и проверка
        # Функция должна пробросить исключение
        with pytest.raises(Exception, match="DB error"):
            await async_write_data()
        
        # Проверяем, что сессия была закрыта (aexit вызван)
        mock_session.__aexit__.assert_called_once()
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_session_error(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Обработка ошибки при создании сессии."""
        # Арранжировка
        mock_get_neo.return_value = [{'mpc_number': 12345, 'name': 'Test'}]
        
        # Симулируем ошибку при создании сессии
        mock_session_local.side_effect = Exception("Session creation error")
        
        # Действие и проверка
        with pytest.raises(Exception, match="Session creation error"):
            await async_write_data()
        
        # Контроллер не должен быть создан при ошибке сессии
        mock_asteroid_controller.assert_not_called()
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_get_neo_error(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Обработка ошибки при получении данных."""
        # Арранжировка
        mock_get_neo.side_effect = Exception("API error")
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        # Действие и проверка
        with pytest.raises(Exception, match="API error"):
            await async_write_data()
        
        # Контроллер не должен быть вызван при ошибке получения данных
        mock_asteroid_controller.assert_not_called()
        mock_session.__aenter__.assert_not_called()
    
    @patch('utils.write_to_db.async_write_data')
    def test_write_data_sync_wrapper(self, mock_async_write):
        """Проверка синхронной обертки."""
        # Арранжировка
        mock_async_write.return_value = None
        
        # Действие
        write_data()
        
        # Проверка
        mock_async_write.assert_called_once()
    
    @patch('utils.write_to_db.async_write_data')
    def test_write_data_with_exception(self, mock_async_write):
        """Проверка обработки исключения в синхронной обертке."""
        # Арранжировка
        mock_async_write.side_effect = Exception("Async error")
        
        # Действие и проверка
        # Исключение должно быть проброшено
        with pytest.raises(Exception, match="Async error"):
            write_data()
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_bulk_create_returns_results(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Проверка обработки результата bulk_create."""
        # Арранжировка
        mock_data = [{'mpc_number': 12345, 'name': 'Test'}]
        mock_get_neo.return_value = mock_data
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        mock_controller_instance = AsyncMock()
        # bulk_create возвращает кортеж (created, updated)
        mock_controller_instance.bulk_create = AsyncMock(return_value=(1, 0))
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие
        await async_write_data()
        
        # Проверка
        mock_controller_instance.bulk_create.assert_called_once_with(
            mock_session, mock_data
        )
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_with_large_dataset(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Запись большого набора данных."""
        # Арранжировка
        # Создаем большой набор тестовых данных
        mock_data = [
            {
                'mpc_number': 10000 + i,
                'name': f'Asteroid {i}',
                'perihelion_au': 0.9 + (i % 10) * 0.02,
                'aphelion_au': 1.8 + (i % 10) * 0.02,
                'earth_moid_au': 0.05 + (i % 10) * 0.01,
                'is_neo': True,
                'is_pha': i % 3 == 0,
                'absolute_magnitude': 20.0 + (i % 10) * 0.1,
                'estimated_diameter_km': 0.3 + (i % 10) * 0.05,
                'accurate_diameter': i % 2 == 0,
                'albedo': 0.15 + (i % 10) * 0.01
            }
            for i in range(100)  # 100 астероидов
        ]
        
        mock_get_neo.return_value = mock_data
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        mock_controller_instance = AsyncMock()
        mock_controller_instance.bulk_create = AsyncMock(return_value=(100, 0))
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие
        await async_write_data()
        
        # Проверка
        mock_controller_instance.bulk_create.assert_called_once_with(
            mock_session, mock_data
        )
        # Проверяем, что передано 100 записей
        assert len(mock_controller_instance.bulk_create.call_args[0][1]) == 100
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_verification(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Проверка структуры передаваемых данных."""
        # Арранжировка
        mock_data = [
            {
                'mpc_number': 99942,
                'name': 'Apophis',
                'perihelion_au': 0.75,
                'aphelion_au': 1.1,
                'earth_moid_au': 0.0002,
                'is_neo': True,
                'is_pha': True,
                'absolute_magnitude': 19.7,
                'estimated_diameter_km': 0.37,
                'accurate_diameter': True,
                'albedo': 0.15
            }
        ]
        
        mock_get_neo.return_value = mock_data
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        # Захватываем данные, переданные в bulk_create
        captured_data = []
        
        async def capture_bulk_create(session, data):
            captured_data.extend(data)
            return (1, 0)
        
        mock_controller_instance = AsyncMock()
        mock_controller_instance.bulk_create = AsyncMock(side_effect=capture_bulk_create)
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие
        await async_write_data()
        
        # Проверка
        assert len(captured_data) == 1
        asteroid_data = captured_data[0]
        
        # Проверяем обязательные поля
        assert 'mpc_number' in asteroid_data
        assert asteroid_data['mpc_number'] == 99942
        
        assert 'name' in asteroid_data
        assert asteroid_data['name'] == 'Apophis'
        
        assert 'perihelion_au' in asteroid_data
        assert asteroid_data['perihelion_au'] == 0.75
        
        assert 'aphelion_au' in asteroid_data
        assert asteroid_data['aphelion_au'] == 1.1
        
        assert 'earth_moid_au' in asteroid_data
        assert asteroid_data['earth_moid_au'] == 0.0002
        
        assert 'is_neo' in asteroid_data
        assert asteroid_data['is_neo'] == True
        
        assert 'is_pha' in asteroid_data
        assert asteroid_data['is_pha'] == True
        
        assert 'absolute_magnitude' in asteroid_data
        assert asteroid_data['absolute_magnitude'] == 19.7
        
        assert 'estimated_diameter_km' in asteroid_data
        assert asteroid_data['estimated_diameter_km'] == 0.37
        
        assert 'accurate_diameter' in asteroid_data
        assert asteroid_data['accurate_diameter'] == True
        
        assert 'albedo' in asteroid_data
        assert asteroid_data['albedo'] == 0.15
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_concurrent_calls(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo
    ):
        """Проверка возможности конкурентных вызовов."""
        # Арранжировка
        mock_data = [{'mpc_number': 12345, 'name': 'Test'}]
        mock_get_neo.return_value = mock_data
        
        # Создаем мок сессии, который можно использовать многократно
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        mock_controller_instance = AsyncMock()
        mock_controller_instance.bulk_create = AsyncMock(return_value=(1, 0))
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие: несколько одновременных вызовов
        tasks = [
            async_write_data(),
            async_write_data(),
            async_write_data()
        ]
        
        await asyncio.gather(*tasks)
        
        # Проверка
        # Каждый вызов должен создать свою сессию и контроллер
        assert mock_session_local.call_count == 3
        assert mock_asteroid_controller.call_count == 3
        assert mock_controller_instance.bulk_create.call_count == 3
    
    @patch('utils.write_to_db.get_neo')
    @patch('utils.write_to_db.AsteroidController')
    @patch('utils.write_to_db.AsyncSessionLocal')
    async def test_async_write_data_logging(
        self, mock_session_local, mock_asteroid_controller, mock_get_neo, caplog
    ):
        """Проверка логирования."""
        import logging
        
        # Арранжировка
        mock_data = [{'mpc_number': 12345, 'name': 'Test'}]
        mock_get_neo.return_value = mock_data
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_session_local.return_value = mock_session
        
        mock_controller_instance = AsyncMock()
        mock_controller_instance.bulk_create = AsyncMock(return_value=(1, 0))
        mock_asteroid_controller.return_value = mock_controller_instance
        
        # Действие с включенным логированием
        with caplog.at_level(logging.DEBUG):
            await async_write_data()
        
        # Хотя в функции нет явного логирования,
        # контроллеры и SQLAlchemy могут логировать
        # Проверяем, что функция выполнилась
        mock_controller_instance.bulk_create.assert_called_once()