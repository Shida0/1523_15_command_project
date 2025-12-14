"""
Тесты для контроллера астероидов.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from sqlalchemy import text
from controllers.asteroid_controller import AsteroidController
from models.asteroid import AsteroidModel

class TestAsteroidController:
    """Тесты контроллера астероидов."""
    
    @pytest.fixture
    def controller(self):
        """Создание контроллера для тестов."""
        return AsteroidController()
    
    @pytest.mark.db
    async def test_get_by_mpc_number_found(self, controller, async_session, test_asteroid):
        """Поиск по номеру MPC."""
        # Действие
        result = await controller.get_by_mpc_number(async_session, test_asteroid.mpc_number)
        
        # Проверка
        assert result is not None
        assert result.id == test_asteroid.id
        assert result.mpc_number == test_asteroid.mpc_number
    
    @pytest.mark.db
    async def test_get_by_mpc_number_not_found(self, controller, async_session):
        """Поиск по несуществующему номеру MPC."""
        # Действие
        result = await controller.get_by_mpc_number(async_session, 999999999)
        
        # Проверка
        assert result is None
    
    @pytest.mark.db
    async def test_get_pha_asteroids(self, controller, async_session):
        """Получение только опасных астероидов."""
        # Создаем тестовые данные
        pha_asteroids = []
        non_pha_asteroids = []
        
        for i in range(3):
            # PHA астероиды
            pha_data = {
                "mpc_number": 111000 + i,
                "name": f"PHA Test {i}",
                "perihelion_au": 0.8,
                "aphelion_au": 1.5,
                "earth_moid_au": 0.03,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.3 + i * 0.1,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True
            }
            pha_asteroids.append(await controller.create(async_session, pha_data))
            
            # Не-PHA астероиды
            non_pha_data = {
                "mpc_number": 222000 + i,
                "name": f"Non-PHA Test {i}",
                "perihelion_au": 1.2,
                "aphelion_au": 2.5,
                "earth_moid_au": 0.1,
                "absolute_magnitude": 19.0,
                "estimated_diameter_km": 0.2 + i * 0.1,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": False
            }
            non_pha_asteroids.append(await controller.create(async_session, non_pha_data))
        
        # Действие
        results = await controller.get_pha_asteroids(async_session, skip=0, limit=10)
        
        # Проверка
        assert len(results) >= 3  # Как минимум наши 3 PHA
        for asteroid in results:
            assert asteroid.is_pha == True
    
    @pytest.mark.db
    async def test_search_by_name_success(self, controller, async_session):
        """Поиск по названию."""
        # Создаем тестовые данные
        test_names = ["Apollo", "Aten", "Amor", "Atira", "Apophis"]
        
        for i, name in enumerate(test_names):
            asteroid_data = {
                "mpc_number": 333000 + i,
                "name": name,
                "designation": f"2024 {name}",
                "perihelion_au": 0.9,
                "aphelion_au": 1.8,
                "earth_moid_au": 0.05,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.3,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True
            }
            await controller.create(async_session, asteroid_data)
        
        # Действие: поиск по "Apo"
        results = await controller.search_by_name(async_session, "Apo", skip=0, limit=10)
        
        # Проверка: должен найти Apollo и Apophis
        assert len(results) >= 2
        names_found = [a.name for a in results]
        assert "Apollo" in names_found or "Apophis" in names_found
    
    @pytest.mark.db
    async def test_search_by_name_no_results(self, controller, async_session):
        """Поиск по названию без результатов."""
        # Действие
        results = await controller.search_by_name(async_session, "NonexistentName", skip=0, limit=10)
        
        # Проверка
        assert len(results) == 0
    
    @pytest.mark.db
    async def test_get_asteroids_by_diameter_range(self, controller, async_session):
        """Фильтрация по диапазону диаметров."""
        # Создаем тестовые данные с разными диаметрами
        test_diameters = [0.1, 0.5, 1.0, 1.5, 2.0]
        
        for i, diameter in enumerate(test_diameters):
            asteroid_data = {
                "mpc_number": 444000 + i,
                "name": f"Diameter Test {i}",
                "perihelion_au": 0.9,
                "aphelion_au": 1.8,
                "earth_moid_au": 0.05,
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": diameter,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": True
            }
            await controller.create(async_session, asteroid_data)
        
        # Тест 1: Диаметр от 0.3 до 1.2 км
        results1 = await controller.get_asteroids_by_diameter_range(
            async_session,
            min_diameter=0.3,
            max_diameter=1.2
        )
        
        # Проверка: должны быть диаметры 0.5 и 1.0
        assert len(results1) >= 2
        diameters_found = [a.estimated_diameter_km for a in results1]
        assert 0.5 in diameters_found
        assert 1.0 in diameters_found
        assert all(0.3 <= d <= 1.2 for d in diameters_found)
        
        # Тест 2: Только минимальный диаметр
        results2 = await controller.get_asteroids_by_diameter_range(
            async_session,
            min_diameter=1.0
        )
        
        # Проверка: должны быть диаметры >= 1.0
        assert len(results2) >= 3  # 1.0, 1.5, 2.0
        assert all(a.estimated_diameter_km >= 1.0 for a in results2)
        
        # Тест 3: Только максимальный диаметр
        results3 = await controller.get_asteroids_by_diameter_range(
            async_session,
            max_diameter=0.8
        )
        
        # Проверка: должны быть диаметры <= 0.8
        assert len(results3) >= 2  # 0.1, 0.5
        assert all(a.estimated_diameter_km <= 0.8 for a in results3)
    
    @pytest.mark.db
    async def test_get_statistics_success(self, controller, async_session):
        """Расчет статистики."""
        # Создаем тестовые данные
        # 3 PHA и 2 не-PHA
        for i in range(5):
            asteroid_data = {
                "mpc_number": 555000 + i,
                "name": f"Stats Test {i}",
                "perihelion_au": 0.8 + i * 0.1,
                "aphelion_au": 1.8 + i * 0.1,
                "earth_moid_au": 0.02 + i * 0.01,
                "absolute_magnitude": 19.0 + i * 0.2,
                "estimated_diameter_km": 0.3 + i * 0.2,
                "accurate_diameter": False,
                "albedo": 0.15,
                "is_neo": True,
                "is_pha": i < 3  # Первые 3 - PHA
            }
            await controller.create(async_session, asteroid_data)
        
        # Действие
        stats = await controller.get_statistics(async_session)
        
        # Проверка
        assert isinstance(stats, dict)
        assert "total_asteroids" in stats
        assert "pha_count" in stats
        assert "percent_pha" in stats
        assert "average_diameter_km" in stats
        assert "min_moid_au" in stats
        assert "last_updated" in stats
        
        # Проверяем правильность расчетов
        assert stats["pha_count"] >= 3
        assert 0 <= stats["percent_pha"] <= 100
        assert stats["min_moid_au"] >= 0
        assert stats["average_diameter_km"] > 0
    
    @pytest.mark.db
    async def test_get_statistics_empty_db(self, controller, async_session):
        """Статистика пустой БД (только тестовые данные)."""
        # Удаляем все тестовые астероиды
        await async_session.execute(text("DELETE FROM asteroid_models WHERE mpc_number >= 999990"))
        await async_session.commit()
        
        # Действие
        stats = await controller.get_statistics(async_session)
        
        # Проверка
        assert stats["total_asteroids"] >= 0
        assert stats["pha_count"] >= 0
        assert stats["percent_pha"] == 0 or stats["percent_pha"] >= 0
        assert stats["min_moid_au"] == 0 or stats["min_moid_au"] >= 0
    
    @pytest.mark.db
    async def test_controller_inherits_base_methods(self, controller, async_session):
        """Проверка, что контроллер наследует базовые методы."""
        # Тестируем метод create
        asteroid_data = {
            "mpc_number": 666000,
            "name": "Inheritance Test",
            "perihelion_au": 0.9,
            "aphelion_au": 1.8,
            "earth_moid_au": 0.05,
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.3,
            "accurate_diameter": False,
            "albedo": 0.15,
            "is_neo": True,
            "is_pha": True
        }
        
        # Действие
        created = await controller.create(async_session, asteroid_data)
        
        # Проверка
        assert created is not None
        assert created.mpc_number == 666000
        
        # Тестируем метод get_by_id
        found = await controller.get_by_id(async_session, created.id)
        assert found is not None
        assert found.id == created.id
        
        # Тестируем метод update
        updated = await controller.update(async_session, created.id, {"name": "Updated Name"})
        assert updated is not None
        assert updated.name == "Updated Name"
        
        # Тестируем метод delete
        deleted = await controller.delete(async_session, created.id)
        assert deleted is True
        
        # Проверяем, что удалено
        not_found = await controller.get_by_id(async_session, created.id)
        assert not_found is None
    
    @pytest.mark.db
    async def test_bulk_create_with_mpc_number_conflict(self, controller, async_session):
        """Массовое создание с конфликтами по mpc_number."""
        # Создаем начальный астероид
        initial_data = {
            "mpc_number": 777000,
            "name": "Initial Asteroid",
            "perihelion_au": 0.9,
            "aphelion_au": 1.8,
            "earth_moid_au": 0.05,
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.3,
            "accurate_diameter": False,
            "albedo": 0.15,
            "is_neo": True,
            "is_pha": True
        }
        await controller.create(async_session, initial_data)
        
        # Подготавливаем данные для массового создания
        data_list = [
            {
                "mpc_number": 777000,  # Конфликт - обновится
                "name": "Updated Asteroid",
                "perihelion_au": 0.95,
                "aphelion_au": 1.85,
                "earth_moid_au": 0.06,
                "absolute_magnitude": 20.1,
                "estimated_diameter_km": 0.35,
                "accurate_diameter": True,
                "albedo": 0.2,
                "is_neo": True,
                "is_pha": False
            },
            {
                "mpc_number": 777001,  # Новая запись
                "name": "New Asteroid",
                "perihelion_au": 0.8,
                "aphelion_au": 1.7,
                "earth_moid_au": 0.04,
                "absolute_magnitude": 19.5,
                "estimated_diameter_km": 0.4,
                "accurate_diameter": False,
                "albedo": 0.18,
                "is_neo": True,
                "is_pha": True
            }
        ]
        
        # Действие
        created, updated = await controller.bulk_create(
            async_session,
            data_list,
            conflict_action="update",
            conflict_fields=["mpc_number"]
        )
        
        # Проверка
        assert created == 1  # Одна новая запись
        assert updated == 1  # Одна обновленная запись
        
        # Проверяем обновленную запись
        updated_asteroid = await controller.get_by_mpc_number(async_session, 777000)
        assert updated_asteroid is not None
        assert updated_asteroid.name == "Updated Asteroid"
        assert updated_asteroid.is_pha == False
        
        # Проверяем новую запись
        new_asteroid = await controller.get_by_mpc_number(async_session, 777001)
        assert new_asteroid is not None
        assert new_asteroid.name == "New Asteroid"