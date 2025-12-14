"""
Тесты для контроллера сближений.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from controllers.approach_controller import ApproachController
from models.close_approach import CloseApproachModel
from models.asteroid import AsteroidModel

class TestApproachController:
    """Тесты контроллера сближений."""
    
    @pytest.fixture
    def controller(self):
        """Создание контроллера для тестов."""
        return ApproachController()
    
    @pytest.fixture
    async def test_asteroids(self, async_session):
        """Создание нескольких тестовых астероидов."""
        asteroids = []
        for i in range(3):
            asteroid = AsteroidModel(
                mpc_number=888000 + i,
                name=f"Approach Test Asteroid {i}",
                perihelion_au=0.9 + i * 0.1,
                aphelion_au=1.8 + i * 0.1,
                earth_moid_au=0.05,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.3 + i * 0.1,
                accurate_diameter=False,
                albedo=0.15,
                is_neo=True,
                is_pha=True
            )
            async_session.add(asteroid)
            asteroids.append(asteroid)
        
        await async_session.flush()
        for asteroid in asteroids:
            await async_session.refresh(asteroid)
        
        return asteroids
    
    @pytest.fixture
    async def test_approaches(self, async_session, test_asteroids):
        """Создание тестовых сближений."""
        approaches = []
        now = datetime.now()
        
        for i, asteroid in enumerate(test_asteroids):
            for j in range(2):  # По 2 сближения на каждый астероид
                approach = CloseApproachModel(
                    asteroid_id=asteroid.id,
                    approach_time=now + timedelta(days=30 * (i + 1) + j * 10),
                    distance_au=0.02 + j * 0.01,
                    velocity_km_s=18.0 + j * 2.0,
                    calculation_batch_id=f"test_batch_{i}_{j}"
                )
                async_session.add(approach)
                approaches.append(approach)
        
        await async_session.flush()
        for approach in approaches:
            await async_session.refresh(approach)
        
        return approaches
    
    @pytest.mark.db
    async def test_get_by_asteroid(self, controller, async_session, test_asteroids, test_approaches):
        """Все сближения конкретного астероида."""
        # Выбираем первый астероид
        asteroid = test_asteroids[0]
        
        # Действие
        results = await controller.get_by_asteroid(async_session, asteroid.id, skip=0, limit=10)
        
        # Проверка
        assert len(results) == 2  # Мы создали по 2 сближения на астероид
        for approach in results:
            assert approach.asteroid_id == asteroid.id
    
    @pytest.mark.db
    async def test_get_approaches_in_period(self, controller, async_session, test_approaches):
        """Сближения в указанном временном периоде."""
        # Определяем период
        start_date = datetime.now() + timedelta(days=20)
        end_date = datetime.now() + timedelta(days=50)
        
        # Действие
        results = await controller.get_approaches_in_period(
            async_session,
            start_date=start_date,
            end_date=end_date,
            max_distance=0.05,
            skip=0,
            limit=10
        )
        
        # Проверка
        for approach in results:
            assert start_date <= approach.approach_time <= end_date
            assert approach.distance_au <= 0.05
    
    @pytest.mark.db
    async def test_get_closest_approaches(self, controller, async_session, test_approaches):
        """Ближайшие по времени сближения."""
        # Действие
        results = await controller.get_closest_approaches(async_session, limit=5)
        
        # Проверка
        assert len(results) <= 5
        
        # Проверяем сортировку по времени (ближайшие сначала)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].approach_time <= results[i + 1].approach_time
    
    @pytest.mark.db
    async def test_get_closest_by_distance(self, controller, async_session, test_approaches):
        """Самые близкие по расстоянию сближения."""
        # Действие
        results = await controller.get_closest_by_distance(async_session, limit=3)
        
        # Проверка
        assert len(results) <= 3
        
        # Проверяем сортировку по расстоянию (ближайшие сначала)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].distance_au <= results[i + 1].distance_au
    
    @pytest.mark.db
    async def test_bulk_create_approaches(self, controller, async_session, test_asteroids):
        """Массовое создание сближений."""
        # Подготавливаем данные
        approaches_data = []
        now = datetime.now()
        
        for i, asteroid in enumerate(test_asteroids):
            approaches_data.append({
                "asteroid_id": asteroid.id,
                "approach_time": now + timedelta(days=30 * (i + 1)),
                "distance_au": 0.03 + i * 0.01,
                "velocity_km_s": 18.5,
                "calculation_batch_id": "test_bulk_001"
            })
        
        # Действие
        saved_count = await controller.bulk_create_approaches(
            async_session,
            approaches_data,
            "test_bulk_batch"
        )
        
        # Проверка
        assert saved_count == len(approaches_data)
        
        # Проверяем, что сближения созданы
        for asteroid in test_asteroids:
            approaches = await controller.get_by_asteroid(async_session, asteroid.id)
            assert len(approaches) >= 1  # Уже были + новые
    
    @pytest.mark.db
    async def test_delete_old_approaches(self, controller, async_session):
        """Удаление устаревших сближений."""
        # Создаем астероид
        asteroid = AsteroidModel(
            mpc_number=889000,
            name="Old Approach Test",
            perihelion_au=0.9,
            aphelion_au=1.8,
            earth_moid_au=0.05,
            absolute_magnitude=20.0,
            estimated_diameter_km=0.3,
            accurate_diameter=False,
            albedo=0.15,
            is_neo=True,
            is_pha=True
        )
        async_session.add(asteroid)
        await async_session.flush()
        await async_session.refresh(asteroid)
        
        # Создаем устаревшее сближение (в прошлом)
        old_approach = CloseApproachModel(
            asteroid_id=asteroid.id,
            approach_time=datetime.now() - timedelta(days=10),
            distance_au=0.02,
            velocity_km_s=18.5,
            calculation_batch_id="test_old_batch"
        )
        async_session.add(old_approach)
        
        # Создаем будущее сближение
        future_approach = CloseApproachModel(
            asteroid_id=asteroid.id,
            approach_time=datetime.now() + timedelta(days=10),
            distance_au=0.03,
            velocity_km_s=19.0,
            calculation_batch_id="test_future_batch"
        )
        async_session.add(future_approach)
        
        await async_session.flush()
        
        # Устанавливаем порог - вчера
        cutoff_date = datetime.now() - timedelta(days=1)
        
        # Действие
        deleted_count = await controller.delete_old_approaches(async_session, cutoff_date)
        
        # Проверка
        assert deleted_count >= 1  # Должен удалить хотя бы одно устаревшее
        
        # Проверяем, что устаревшее удалено
        approaches = await controller.get_by_asteroid(async_session, asteroid.id)
        for approach in approaches:
            assert approach.approach_time > cutoff_date
    
    @pytest.mark.db
    async def test_get_approaches_with_threats(self, controller, async_session, test_asteroids):
        """Сближения с оценками угроз."""
        # Создаем сближение с оценкой угрозы
        from models.threat_assessment import ThreatAssessmentModel
        
        asteroid = test_asteroids[0]
        now = datetime.now()
        
        # Создаем сближение
        approach = CloseApproachModel(
            asteroid_id=asteroid.id,
            approach_time=now + timedelta(days=30),
            distance_au=0.02,
            velocity_km_s=18.5,
            calculation_batch_id="test_threat_batch"
        )
        async_session.add(approach)
        await async_session.flush()
        await async_session.refresh(approach)
        
        # Создаем оценку угрозы
        threat = ThreatAssessmentModel(
            approach_id=approach.id,
            threat_level="высокий",
            impact_category="региональный",
            energy_megatons=15.5
        )
        async_session.add(threat)
        await async_session.flush()
        
        # Явно коммитим изменения
        await async_session.commit()
        
        # Создаем новую сессию для теста, чтобы проверить загрузку из БД
        from sqlalchemy.ext.asyncio import AsyncSession
        from models.engine import AsyncSessionLocal
        
        async with AsyncSessionLocal() as new_session:
            # Действие 1: все сближения с оценками
            results1 = await controller.get_approaches_with_threats(
                new_session,
                threat_level=None,
                start_date=None,
                end_date=None,
                skip=0,
                limit=10
            )
            
            # Проверка
            assert len(results1) >= 1
            assert hasattr(results1[0], 'threat_assessment')
            assert results1[0].threat_assessment is not None
            assert results1[0].threat_assessment.threat_level == "высокий"
            
            # Действие 2: фильтрация по уровню угрозы
            results2 = await controller.get_approaches_with_threats(
                new_session,
                threat_level="высокий",
                start_date=None,
                end_date=None,
                skip=0,
                limit=10
            )
            
            # Проверка
            for result in results2:
                assert result.threat_assessment.threat_level == "высокий"
            
            # Действие 3: фильтрация по дате
            start_date = now + timedelta(days=20)
            end_date = now + timedelta(days=40)
            results3 = await controller.get_approaches_with_threats(
                new_session,
                threat_level=None,
                start_date=start_date,
                end_date=end_date,
                skip=0,
                limit=10
            )
            
            # Проверка
            for result in results3:
                assert start_date <= result.approach_time <= end_date
    
    @pytest.mark.db
    async def test_controller_inherits_base_methods(self, controller, async_session, test_asteroids):
        """Проверка, что контроллер наследует базовые методы."""
        # Создаем тестовое сближение
        asteroid = test_asteroids[0]
        now = datetime.now()
        
        approach_data = {
            "asteroid_id": asteroid.id,
            "approach_time": now + timedelta(days=30),
            "distance_au": 0.025,
            "velocity_km_s": 18.7,
            "calculation_batch_id": "test_inheritance"
        }
        
        # Тестируем метод create
        created = await controller.create(async_session, approach_data)
        assert created is not None
        assert created.asteroid_id == asteroid.id
        
        # Тестируем метод get_by_id
        found = await controller.get_by_id(async_session, created.id)
        assert found is not None
        assert found.id == created.id
        
        # Тестируем метод update
        updated = await controller.update(async_session, created.id, {"velocity_km_s": 20.0})
        assert updated is not None
        assert updated.velocity_km_s == 20.0
        
        # Тестируем метод delete
        deleted = await controller.delete(async_session, created.id)
        assert deleted is True
        
        # Проверяем, что удалено
        not_found = await controller.get_by_id(async_session, created.id)
        assert not_found is None
    
    @pytest.mark.db
    async def test_distance_conversion_on_create(self, controller, async_session, test_asteroids):
        """Проверка автоматического преобразования расстояния при создании."""
        asteroid = test_asteroids[0]
        now = datetime.now()
        
        # Создаем сближение только с distance_au
        approach_data = {
            "asteroid_id": asteroid.id,
            "approach_time": now + timedelta(days=45),
            "distance_au": 0.035,
            "velocity_km_s": 19.2,
            "calculation_batch_id": "test_distance_conversion"
        }
        
        # Действие
        created = await controller.create(async_session, approach_data)
        
        # Проверка: distance_km должно быть рассчитано автоматически
        assert created.distance_km is not None
        assert created.distance_km == 0.035 * 149597870.7  # 1 а.е. в км
    
    @pytest.mark.db
    async def test_validation_distance_too_far(self, controller, async_session, test_asteroids):
        """Валидация: сближение дальше 1 а.е. не должно сохраняться."""
        asteroid = test_asteroids[0]
        now = datetime.now()
        
        # Пытаемся создать сближение дальше 1 а.е.
        approach_data = {
            "asteroid_id": asteroid.id,
            "approach_time": now + timedelta(days=60),
            "distance_au": 1.5,  # > 1.0 а.е.
            "velocity_km_s": 17.8,
            "calculation_batch_id": "test_too_far"
        }
        
        # Действие и проверка: должно вызвать ValueError
        with pytest.raises(ValueError, match="Храним только сближения ближе 1 а.е."):
            await controller.create(async_session, approach_data)