"""
Тесты для базового контроллера.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from controllers.base_controller import BaseController
from models.asteroid import AsteroidModel

class TestBaseController:
    """Тесты базового контроллера."""
    
    @pytest.fixture
    def controller(self):
        """Создание контроллера для тестов."""
        return BaseController(AsteroidModel)
    
    @pytest.fixture
    def sample_data(self):
        """Тестовые данные для создания."""
        return {
            "mpc_number": 999999,
            "name": "Test Controller Asteroid",
            "perihelion_au": 1.0,
            "aphelion_au": 2.0,
            "earth_moid_au": 0.1,
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.5,
            "accurate_diameter": False,
            "albedo": 0.15,
            "is_neo": True,
            "is_pha": True
        }
    
    @pytest.mark.db
    async def test_create_success(self, controller, async_session, sample_data):
        """Успешное создание записи."""
        # Действие
        result = await controller.create(async_session, sample_data)
        
        # Проверка
        assert result is not None
        assert result.id is not None
        assert result.mpc_number == sample_data["mpc_number"]
        assert result.name == sample_data["name"]
        
        # Проверяем, что запись можно найти
        found = await controller.get_by_id(async_session, result.id)
        assert found is not None
        assert found.id == result.id
    
    @pytest.mark.db
    async def test_create_with_invalid_data(self, controller, async_session):
        """Создание с некорректными данными."""
        # Арранжировка - данные с неверным альбедо
        invalid_data = {
            "mpc_number": 999998,
            "perihelion_au": 1.0,
            "aphelion_au": 2.0,
            "earth_moid_au": 0.1,
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.5,
            "accurate_diameter": False,
            "albedo": 1.5,  # Неверное альбедо (> 1)
            "is_neo": True,
            "is_pha": True
        }
        
        # Действие и проверка
        with pytest.raises(ValueError):
            await controller.create(async_session, invalid_data)
    
    async def test_create_with_exception(self, controller, mock_async_session, sample_data):
        """Обработка исключений при создании."""
        # Настраиваем mock для правильной эмуляции исключения
        mock_async_session.flush.side_effect = SQLAlchemyError("DB error")
        
        # Действие и проверка
        with pytest.raises(SQLAlchemyError):
            await controller.create(mock_async_session, sample_data)
        
        # Проверяем, что был откат
        mock_async_session.rollback.assert_called_once()
    
    @pytest.mark.db
    async def test_get_by_id_found(self, controller, async_session, test_asteroid):
        """Поиск существующей записи."""
        # Действие
        result = await controller.get_by_id(async_session, test_asteroid.id)
        
        # Проверка
        assert result is not None
        assert result.id == test_asteroid.id
        assert result.name == test_asteroid.name
    
    @pytest.mark.db
    async def test_get_by_id_not_found(self, controller, async_session):
        """Поиск несуществующей записи."""
        # Действие
        result = await controller.get_by_id(async_session, 999999)
        
        # Проверка
        assert result is None
    
    @pytest.mark.db
    async def test_update_success(self, controller, async_session, test_asteroid):
        """Успешное обновление."""
        # Арранжировка
        update_data = {"name": "Updated Name", "is_pha": False}
        
        # Действие
        result = await controller.update(async_session, test_asteroid.id, update_data)
        
        # Проверка
        assert result is not None
        assert result.name == "Updated Name"
        assert result.is_pha == False
        # Проверяем, что другие поля не изменились
        assert result.mpc_number == test_asteroid.mpc_number
    
    @pytest.mark.db
    async def test_update_not_found(self, controller, async_session):
        """Обновление несуществующей записи."""
        # Действие
        result = await controller.update(async_session, 999999, {"name": "Test"})
        
        # Проверка
        assert result is None
    
    @pytest.mark.db
    async def test_delete_success(self, controller, async_session, test_asteroid):
        """Успешное удаление."""
        # Действие
        result = await controller.delete(async_session, test_asteroid.id)
        
        # Проверка
        assert result is True
        
        # Проверяем, что запись удалена
        found = await controller.get_by_id(async_session, test_asteroid.id)
        assert found is None
    
    @pytest.mark.db
    async def test_delete_not_found(self, controller, async_session):
        """Удаление несуществующей записи."""
        # Действие
        result = await controller.delete(async_session, 999999)
        
        # Проверка
        assert result is False
    
    @pytest.mark.db
    async def test_get_all_with_pagination(self, controller, async_session):
        """Пагинация."""
        # Создаем несколько тестовых записей
        for i in range(5):
            asteroid_data = {
                "mpc_number": 100000 + i,
                "name": f"Test Asteroid {i}",
                "perihelion_au": 1.0 + i * 0.1,
                "aphelion_au": 2.0 + i * 0.1,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.5,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True if i % 2 == 0 else False
            }
            await controller.create(async_session, asteroid_data)
        
        # Действие 1: первые 2 записи
        result1 = await controller.get_all(async_session, skip=0, limit=2)
        assert len(result1) == 2
        
        # Действие 2: пропустить 2, взять 2
        result2 = await controller.get_all(async_session, skip=2, limit=2)
        assert len(result2) == 2
        
        # Проверяем, что результаты разные
        assert result1[0].mpc_number != result2[0].mpc_number
    
    @pytest.mark.db
    async def test_count_records(self, controller, async_session):
        """Подсчет записей."""
        # Сначала очищаем тестовые данные
        await async_session.execute(text("DELETE FROM asteroid_models WHERE mpc_number >= 999990"))
        await async_session.commit()
        
        # Создаем 3 записи
        for i in range(3):
            asteroid_data = {
                "mpc_number": 999990 + i,
                "name": f"Count Test {i}",
                "perihelion_au": 1.0,
                "aphelion_au": 2.0,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.5,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True
            }
            await controller.create(async_session, asteroid_data)
        
        # Действие
        count = await controller.count(async_session)
        
        # Проверка - должно быть как минимум 3 записи
        assert count >= 3
    
    @pytest.mark.db
    async def test_filter_basic(self, controller, async_session, test_asteroid):
        """Базовая фильтрация."""
        # Действие
        results = await controller.filter(async_session, {"is_pha": True})
        
        # Проверка
        assert len(results) > 0
        for result in results:
            assert result.is_pha == True
    
    @pytest.mark.db
    async def test_filter_with_operators(self, controller, async_session):
        """Фильтрация с операторами."""
        # Создаем тестовые записи с разными диаметрами
        test_data = [
            {"mpc_number": 999901, "estimated_diameter_km": 0.1, "is_pha": True},
            {"mpc_number": 999902, "estimated_diameter_km": 0.5, "is_pha": True},
            {"mpc_number": 999903, "estimated_diameter_km": 1.0, "is_pha": False},
        ]
        
        for data in test_data:
            asteroid_data = {
                "name": "Filter Test",
                "perihelion_au": 1.0,
                "aphelion_au": 2.0,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 20.0,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                **data
            }
            await controller.create(async_session, asteroid_data)
        
        # Тест 1: диаметр больше 0.3
        results1 = await controller.filter(async_session, {"estimated_diameter_km__gt": 0.3})
        assert len(results1) >= 2  # 0.5 и 1.0
        
        # Тест 2: диаметр меньше 0.8
        results2 = await controller.filter(async_session, {"estimated_diameter_km__lt": 0.8})
        assert len(results2) >= 2  # 0.1 и 0.5
        
        # Тест 3: комбинированный фильтр
        results3 = await controller.filter(async_session, {
            "estimated_diameter_km__gt": 0.2,
            "estimated_diameter_km__lt": 0.8,
            "is_pha": True
        })
        assert len(results3) >= 1  # только 0.5
    
    @pytest.mark.db
    async def test_filter_with_order(self, controller, async_session):
        """Фильтрация с сортировкой."""
        # Создаем записи с разными диаметрами
        diameters = [0.3, 0.1, 0.5, 0.2, 0.4]
        
        for i, diameter in enumerate(diameters):
            asteroid_data = {
                "mpc_number": 999910 + i,
                "name": f"Sort Test {i}",
                "perihelion_au": 1.0,
                "aphelion_au": 2.0,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": diameter,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True
            }
            await controller.create(async_session, asteroid_data)
        
        # Действие: сортировка по диаметру
        results = await controller.filter(
            async_session,
            filters={},
            order_by="estimated_diameter_km"
        )
        
        # Проверка: должны быть отсортированы по возрастанию
        diameters_sorted = [r.estimated_diameter_km for r in results[:5]]
        assert diameters_sorted == sorted(diameters_sorted)
    
    @pytest.mark.db
    async def test_bulk_create_success(self, controller, async_session):
        """Массовое создание."""
        # Арранжировка
        data_list = [
            {
                "mpc_number": 999921,
                "name": "Bulk Test 1",
                "perihelion_au": 1.0,
                "aphelion_au": 2.0,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.5,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True
            },
            {
                "mpc_number": 999922,
                "name": "Bulk Test 2",
                "perihelion_au": 1.1,
                "aphelion_au": 2.1,
                "earth_moid_au": 0.2,
                "absolute_magnitude": 21.0,
                "estimated_diameter_km": 0.6,
                "accurate_diameter": True,
                "albedo": 0.2,
                "is_neo": True,
                "is_pha": False
            }
        ]
        
        # Действие
        created, updated = await controller.bulk_create(async_session, data_list)
        
        # Проверка
        assert created == 2
        assert updated == 0
        
        # Проверяем, что записи созданы
        count = await controller.count(async_session)
        assert count >= 2
    
    @pytest.mark.db
    async def test_search_success(self, controller, async_session):
        """Поиск по текстовым полям."""
        # Создаем тестовые записи
        test_asteroids = [
            {"mpc_number": 999931, "name": "Apollo", "designation": "1862 Apollo"},
            {"mpc_number": 999932, "name": "Aten", "designation": "2062 Aten"},
            {"mpc_number": 999933, "name": "Amor", "designation": "1221 Amor"},
        ]
        
        for asteroid in test_asteroids:
            asteroid_data = {
                "perihelion_au": 1.0,
                "aphelion_au": 2.0,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.5,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True,
                **asteroid
            }
            await controller.create(async_session, asteroid_data)
        
        # Действие: поиск по "Apollo"
        results = await controller.search(
            async_session,
            search_term="Apollo",
            search_fields=["name", "designation"]
        )
        
        # Проверка
        assert len(results) >= 1
        assert any("Apollo" in r.name for r in results)
    
    def test_build_filter_conditions(self, controller):
        """Построение условий фильтрации."""
        # Арранжировка
        filters = {
            "is_pha": True,
            "estimated_diameter_km__gt": 0.1,
            "estimated_diameter_km__lt": 1.0,
            "name__ilike": "test"
        }
        
        # Действие
        conditions = controller._build_filter_conditions(filters)
        
        # Проверка
        assert len(conditions) == 4
        # Проверяем типы условий
        for condition in conditions:
            assert hasattr(condition, '__str__')