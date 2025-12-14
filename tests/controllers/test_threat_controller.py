"""
Тесты для контроллера оценок угроз.
"""
import pytest
from unittest.mock import AsyncMock
from controllers.threat_controller import ThreatController
from models.threat_assessment import ThreatAssessmentModel
from models.close_approach import CloseApproachModel
from models.asteroid import AsteroidModel

class TestThreatController:
    """Тесты контроллера оценок угроз."""
    
    @pytest.fixture
    def controller(self):
        """Создание контроллера для тестов."""
        return ThreatController()
    
    @pytest.fixture
    async def test_asteroid_with_approaches(self, async_session):
        """Создание астероида со сближениями."""
        # Создаем астероид
        asteroid = AsteroidModel(
            mpc_number=900000,
            name="Threat Test Asteroid",
            perihelion_au=0.85,
            aphelion_au=1.75,
            earth_moid_au=0.04,
            absolute_magnitude=19.5,
            estimated_diameter_km=0.45,
            accurate_diameter=True,
            albedo=0.22,
            is_neo=True,
            is_pha=True
        )
        async_session.add(asteroid)
        await async_session.flush()
        await async_session.refresh(asteroid)
        
        # Создаем несколько сближений
        from datetime import datetime, timedelta
        now = datetime.now()
        
        approaches = []
        for i in range(3):
            approach = CloseApproachModel(
                asteroid_id=asteroid.id,
                approach_time=now + timedelta(days=30 * (i + 1)),
                distance_au=0.02 + i * 0.01,
                velocity_km_s=18.0 + i * 1.0,
                calculation_batch_id=f"threat_test_batch_{i}"
            )
            async_session.add(approach)
            approaches.append(approach)
        
        await async_session.flush()
        for approach in approaches:
            await async_session.refresh(approach)
        
        return asteroid, approaches
    
    @pytest.fixture
    async def test_threat_assessments(self, async_session, test_asteroid_with_approaches):
        """Создание тестовых оценок угроз."""
        asteroid, approaches = test_asteroid_with_approaches
        
        threat_levels = ["низкий", "средний", "высокий"]
        impact_categories = ["локальный", "региональный", "региональный"]
        
        assessments = []
        for i, approach in enumerate(approaches):
            threat = ThreatAssessmentModel(
                approach_id=approach.id,
                threat_level=threat_levels[i],
                impact_category=impact_categories[i],
                energy_megatons=5.0 + i * 5.0
            )
            async_session.add(threat)
            assessments.append(threat)
        
        await async_session.flush()
        for assessment in assessments:
            await async_session.refresh(assessment)
        
        return assessments
    
    @pytest.mark.db
    async def test_get_by_approach_id(self, controller, async_session, test_threat_assessments):
        """Оценка угрозы для конкретного сближения."""
        # Берем первую оценку
        test_assessment = test_threat_assessments[0]
        
        # Действие
        result = await controller.get_by_approach_id(async_session, test_assessment.approach_id)
        
        # Проверка
        assert result is not None
        assert result.id == test_assessment.id
        assert result.approach_id == test_assessment.approach_id
        assert result.threat_level == test_assessment.threat_level
    
    @pytest.mark.db
    async def test_get_by_approach_id_not_found(self, controller, async_session):
        """Оценка для несуществующего сближения."""
        # Действие
        result = await controller.get_by_approach_id(async_session, 999999)
        
        # Проверка
        assert result is None
    
    @pytest.mark.db
    async def test_get_high_threats(self, controller, async_session, test_threat_assessments):
        """Оценки с высоким уровнем угрозы."""
        # Действие
        results = await controller.get_high_threats(async_session, limit=10)
        
        # Проверка
        for result in results:
            assert result.threat_level in ["высокий", "критический"]
        
        # Проверяем сортировку по энергии (убывание)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].energy_megatons >= results[i + 1].energy_megatons
    
    @pytest.mark.db
    async def test_update_assessment_success(self, controller, async_session, test_threat_assessments):
        """Обновление оценки."""
        # Берем первую оценку
        test_assessment = test_threat_assessments[0]
        old_hash = test_assessment.calculation_input_hash
        
        # Данные для обновления
        new_data = {
            "threat_level": "критический",
            "impact_category": "глобальный",
            "energy_megatons": 25.5
        }
        
        # Действие
        result = await controller.update_assessment(
            async_session,
            test_assessment.approach_id,
            new_data
        )
        
        # Проверка
        assert result is not None
        assert result.threat_level == "критический"
        assert result.impact_category == "глобальный"
        assert result.energy_megatons == 25.5
        
        # Хеш должен обновиться
        assert result.calculation_input_hash != old_hash
        assert result.calculation_input_hash == result._calculate_input_hash()
    
    @pytest.mark.db
    async def test_update_assessment_not_found(self, controller, async_session):
        """Обновление несуществующей оценки."""
        # Действие
        result = await controller.update_assessment(
            async_session,
            999999,
            {"threat_level": "высокий"}
        )
        
        # Проверка
        assert result is None
    
    @pytest.mark.db
    async def test_bulk_create_assessments(self, controller, async_session, test_asteroid_with_approaches):
        """Массовое создание оценок."""
        asteroid, approaches = test_asteroid_with_approaches
        
        # Подготавливаем данные
        assessments_data = []
        for i, approach in enumerate(approaches):
            assessments_data.append({
                "approach_id": approach.id,
                "threat_level": ["низкий", "средний", "высокий"][i],
                "impact_category": ["локальный", "региональный", "региональный"][i],
                "energy_megatons": 3.0 + i * 4.0
            })
        
        # Добавляем еще одну с тем же approach_id (для проверки обновления)
        assessments_data.append({
            "approach_id": approaches[0].id,  # Конфликт
            "threat_level": "критический",
            "impact_category": "глобальный",
            "energy_megatons": 50.0
        })
        
        # Действие
        saved_count = await controller.bulk_create_assessments(
            async_session,
            assessments_data
        )
        
        # Проверка
        # Должно быть создано 3 новых + 1 обновленная = 4
        assert saved_count == 4
        
        # Проверяем, что первая оценка обновилась
        first_assessment = await controller.get_by_approach_id(async_session, approaches[0].id)
        assert first_assessment is not None
        assert first_assessment.threat_level == "критический"
        assert first_assessment.energy_megatons == 50.0
    
    @pytest.mark.db
    async def test_get_statistics(self, controller, async_session, test_threat_assessments):
        """Статистика по оценкам."""
        # Действие
        stats = await controller.get_statistics(async_session)
        
        # Проверка
        assert isinstance(stats, dict)
        assert "total_assessments" in stats
        assert "threat_levels" in stats
        assert "average_energy_mt" in stats
        assert "max_energy_mt" in stats
        assert "high_threat_count" in stats
        
        # Проверяем структуру threat_levels
        threat_levels = stats["threat_levels"]
        expected_levels = ["низкий", "средний", "высокий", "критический"]
        
        for level in expected_levels:
            assert level in threat_levels
            assert "count" in threat_levels[level]
            assert "percent" in threat_levels[level]
        
        # Проверяем расчеты
        assert stats["total_assessments"] >= len(test_threat_assessments)
        assert stats["high_threat_count"] >= 1  # У нас есть "высокий"
        assert stats["average_energy_mt"] >= 0
        assert stats["max_energy_mt"] >= 0
    
    @pytest.mark.db
    async def test_get_threats_by_asteroid(self, controller, async_session, test_asteroid_with_approaches):
        """Оценки для конкретного астероида."""
        asteroid, approaches = test_asteroid_with_approaches
        
        # Создаем оценки для всех сближений
        for i, approach in enumerate(approaches):
            threat = ThreatAssessmentModel(
                approach_id=approach.id,
                threat_level=["низкий", "средний", "высокий"][i],
                impact_category=["локальный", "региональный", "региональный"][i],
                energy_megatons=2.0 + i * 3.0
            )
            async_session.add(threat)
        
        await async_session.flush()
        
        # Действие
        results = await controller.get_threats_by_asteroid(async_session, asteroid.id)
        
        # Проверка
        assert len(results) == len(approaches)
        
        # Проверяем сортировку по времени сближения
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].close_approach.approach_time <= results[i + 1].close_approach.approach_time
    
    @pytest.mark.db
    async def test_controller_inherits_base_methods(self, controller, async_session, test_asteroid_with_approaches):
        """Проверка, что контроллер наследует базовые методы."""
        asteroid, approaches = test_asteroid_with_approaches
        approach = approaches[0]
        
        # Тестируем метод create
        threat_data = {
            "approach_id": approach.id,
            "threat_level": "средний",
            "impact_category": "региональный",
            "energy_megatons": 12.5
        }
        
        created = await controller.create(async_session, threat_data)
        assert created is not None
        assert created.approach_id == approach.id
        
        # Тестируем метод get_by_id
        found = await controller.get_by_id(async_session, created.id)
        assert found is not None
        assert found.id == created.id
        
        # Тестируем метод update
        updated = await controller.update(async_session, created.id, {"energy_megatons": 15.0})
        assert updated is not None
        assert updated.energy_megatons == 15.0
        
        # Тестируем метод delete
        deleted = await controller.delete(async_session, created.id)
        assert deleted is True
        
        # Проверяем, что удалено
        not_found = await controller.get_by_id(async_session, created.id)
        assert not_found is None
    
    @pytest.mark.db
    async def test_auto_hash_calculation(self, controller, async_session, test_asteroid_with_approaches):
        """Автоматический расчет хеша при создании."""
        asteroid, approaches = test_asteroid_with_approaches
        approach = approaches[0]
        
        # Создаем оценку без указания хеша
        threat_data = {
            "approach_id": approach.id,
            "threat_level": "высокий",
            "impact_category": "региональный",
            "energy_megatons": 20.0
        }
        
        # Действие
        created = await controller.create(async_session, threat_data)
        
        # Проверка
        assert created.calculation_input_hash is not None
        assert created.calculation_input_hash == created._calculate_input_hash()
        
        # Изменяем данные - хеш должен измениться
        old_hash = created.calculation_input_hash
        
        updated = await controller.update(async_session, created.id, {"energy_megatons": 25.0})
        assert updated.calculation_input_hash != old_hash
        assert updated.calculation_input_hash == updated._calculate_input_hash()
    
    @pytest.mark.db
    async def test_validation_threat_level(self, controller, async_session, test_asteroid_with_approaches):
        """Валидация уровня угрозы."""
        asteroid, approaches = test_asteroid_with_approaches
        approach = approaches[0]
        
        # Пытаемся создать с некорректным уровнем угрозы
        threat_data = {
            "approach_id": approach.id,
            "threat_level": "неверный_уровень",  # Некорректное значение
            "impact_category": "региональный",
            "energy_megatons": 10.0
        }
        
        # Действие и проверка: должно вызвать исключение
        # SQLAlchemy проверяет ограничения при flush/commit
        try:
            created = await controller.create(async_session, threat_data)
            await async_session.flush()
            pytest.fail("Должно было вызвать исключение")
        except Exception as e:
            # Проверяем, что это связано с проверочным ограничением
            assert "check_threat_level" in str(e) or "CHECK" in str(e)
            await async_session.rollback()
    
    @pytest.mark.db
    async def test_validation_energy_non_negative(self, controller, async_session, test_asteroid_with_approaches):
        """Валидация неотрицательной энергии."""
        asteroid, approaches = test_asteroid_with_approaches
        approach = approaches[0]
        
        # Пытаемся создать с отрицательной энергией
        threat_data = {
            "approach_id": approach.id,
            "threat_level": "низкий",
            "impact_category": "локальный",
            "energy_megatons": -5.0  # Отрицательное значение
        }
        
        # Действие и проверка: должно вызвать исключение
        try:
            created = await controller.create(async_session, threat_data)
            await async_session.flush()
            pytest.fail("Должно было вызвать исключение")
        except Exception as e:
            # Проверяем, что это связано с проверочным ограничением
            assert "check_energy_non_negative" in str(e) or "CHECK" in str(e)
            await async_session.rollback()