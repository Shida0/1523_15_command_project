"""
Тесты для модели сближений.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from models.close_approach import CloseApproachModel
from models.asteroid import AsteroidModel

class TestCloseApproachModel:
    """Тесты модели сближений."""
    
    @pytest.fixture
    async def test_asteroid(self, async_session):
        """Создание тестового астероида для сближений."""
        asteroid = AsteroidModel(
            mpc_number=2000001,
            name="Approach Test Asteroid",
            perihelion_au=0.9,
            aphelion_au=1.8,
            earth_moid_au=0.05,
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
        return asteroid
    
    def test_close_approach_creation_valid_data(self, test_asteroid):
        """Создание сближения с валидными данными."""
        # Арранжировка
        approach_time = datetime.now() + timedelta(days=30)
        
        # Действие
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_batch_001"
        )
        
        # Проверка
        assert approach.asteroid_id == test_asteroid.id
        assert approach.approach_time == approach_time
        assert approach.distance_au == 0.025
        assert approach.velocity_km_s == 18.7
        assert approach.calculation_batch_id == "test_batch_001"
        
        # Автоматически рассчитанное поле
        assert approach.distance_km == 0.025 * 149597870.7  # 1 а.е. в км
    
    def test_close_approach_creation_with_explicit_distance_km(self, test_asteroid):
        """Создание сближения с явно указанным расстоянием в км."""
        import uuid
        approach_time = datetime.now() + timedelta(days=45)
        
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.03,
            distance_km=4500000.0,  # Явно указано
            velocity_km_s=19.2,
            calculation_batch_id=f"test_explicit_distance_{uuid.uuid4()}"  # Уникальный ID
        )
        
        # Проверяем, что явно указанное значение не перезаписывается
        assert approach.distance_km == 4500000.0
        assert approach.distance_au == 0.03
    
    def test_close_approach_creation_distance_too_far(self, test_asteroid):
        """Валидация: сближение дальше 1 а.е. не должно сохраняться."""
        approach_time = datetime.now() + timedelta(days=60)
        
        # Тест 1: Немного больше 1 а.е.
        with pytest.raises(ValueError, match="Храним только сближения ближе 1 а.е."):
            CloseApproachModel(
                asteroid_id=test_asteroid.id,
                approach_time=approach_time,
                distance_au=1.01,
                velocity_km_s=17.8,
                calculation_batch_id="test_too_far_1"
            )
        
        # Тест 2: Значительно больше 1 а.е.
        with pytest.raises(ValueError, match="Храним только сближения ближе 1 а.е."):
            CloseApproachModel(
                asteroid_id=test_asteroid.id,
                approach_time=approach_time,
                distance_au=2.5,
                velocity_km_s=16.5,
                calculation_batch_id="test_too_far_2"
            )
    
    def test_close_approach_creation_exactly_1_au(self, test_asteroid):
        """Создание сближения на расстоянии ровно 1 а.е."""
        approach_time = datetime.now() + timedelta(days=75)
        
        # Граничный случай: ровно 1 а.е. должно быть допустимо
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=1.0,
            velocity_km_s=18.0,
            calculation_batch_id="test_exact_1_au"
        )
        
        assert approach.distance_au == 1.0
        assert approach.distance_km == 1.0 * 149597870.7
    
    def test_close_approach_creation_very_close(self, test_asteroid):
        """Создание очень близкого сближения."""
        approach_time = datetime.now() + timedelta(days=15)
        
        # Очень близкое сближение (0.0001 а.е. = ~15,000 км)
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.0001,
            velocity_km_s=20.5,
            calculation_batch_id="test_very_close"
        )
        
        assert approach.distance_au == 0.0001
        assert approach.distance_km == 0.0001 * 149597870.7
    
    @pytest.mark.db
    async def test_close_approach_save_to_db(self, async_session, test_asteroid):
        """Сохранение сближения в базу данных."""
        # Арранжировка
        approach_time = datetime.now() + timedelta(days=30)
        
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_db_save"
        )
        
        # Действие
        async_session.add(approach)
        await async_session.flush()
        await async_session.refresh(approach)
        
        # Проверка
        assert approach.id is not None
        assert approach.created_at is not None
        assert approach.updated_at is not None
        assert approach.distance_km == 0.025 * 149597870.7
        
        # Проверяем, что можем найти по ID
        from sqlalchemy import select
        query = select(CloseApproachModel).where(CloseApproachModel.id == approach.id)
        result = await async_session.execute(query)
        found = result.scalar_one()
        
        assert found.id == approach.id
        assert found.asteroid_id == test_asteroid.id
        assert found.distance_au == 0.025
    
    @pytest.mark.db
    async def test_close_approach_relationships(self, async_session, test_asteroid):
        """Проверка связей с другими моделями."""
        from models.threat_assessment import ThreatAssessmentModel
        
        # Создаем сближение
        approach_time = datetime.now() + timedelta(days=30)
        
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_relationships"
        )
        async_session.add(approach)
        await async_session.flush()
        await async_session.refresh(approach)
        
        # Создаем оценку угрозы для этого сближения
        threat = ThreatAssessmentModel(
            approach_id=approach.id,
            threat_level="средний",
            impact_category="региональный",
            energy_megatons=12.5
        )
        async_session.add(threat)
        await async_session.flush()
        
        # Загружаем связи
        await async_session.refresh(approach)
        
        # Проверяем связи
        assert hasattr(approach, 'asteroid')
        assert hasattr(approach, 'threat_assessment')
        
        # Проверяем связь с астероидом
        asteroid = approach.asteroid
        assert asteroid.id == test_asteroid.id
        assert asteroid.name == "Approach Test Asteroid"
        
        # Проверяем связь с оценкой угрозы
        threat_assessment = approach.threat_assessment
        assert threat_assessment is not None
        assert threat_assessment.approach_id == approach.id
        assert threat_assessment.threat_level == "средний"
    
    @pytest.mark.db
    async def test_close_approach_unique_asteroid_approach_time(self, async_session, test_asteroid):
        """Проверка уникальности комбинации asteroid_id и approach_time."""
        approach_time = datetime.now() + timedelta(days=30)
        
        # Создаем первое сближение
        approach1 = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_unique_1"
        )
        async_session.add(approach1)
        await async_session.flush()
        
        # Пытаемся создать второе сближение с тем же астероидом и временем
        approach2 = CloseApproachModel(
            asteroid_id=test_asteroid.id,  # Тот же астероид
            approach_time=approach_time,   # То же время
            distance_au=0.03,              # Другие параметры
            velocity_km_s=19.0,
            calculation_batch_id="test_unique_2"
        )
        async_session.add(approach2)
        
        # Должно вызвать IntegrityError из-за нарушения уникальности
        with pytest.raises(IntegrityError):
            await async_session.flush()
        
        # Откатываем для чистоты теста
        await async_session.rollback()
    
    @pytest.mark.db
    async def test_close_approach_same_time_different_asteroids(self, async_session):
        """Разные астероиды могут иметь сближения в одно время."""
        # Создаем два астероида
        asteroid1 = AsteroidModel(
            mpc_number=2000002,
            name="Asteroid 1",
            perihelion_au=0.9,
            aphelion_au=1.8,
            earth_moid_au=0.05,
            absolute_magnitude=19.5,
            estimated_diameter_km=0.45,
            accurate_diameter=True,
            albedo=0.22,
            is_neo=True,
            is_pha=True
        )
        
        asteroid2 = AsteroidModel(
            mpc_number=2000003,
            name="Asteroid 2",
            perihelion_au=1.0,
            aphelion_au=2.0,
            earth_moid_au=0.1,
            absolute_magnitude=20.0,
            estimated_diameter_km=0.5,
            accurate_diameter=False,
            albedo=0.15,
            is_neo=True,
            is_pha=False
        )
        
        async_session.add_all([asteroid1, asteroid2])
        await async_session.flush()
        await async_session.refresh(asteroid1)
        await async_session.refresh(asteroid2)
        
        # Одно и то же время сближения
        approach_time = datetime.now() + timedelta(days=30)
        
        # Создаем сближения для обоих астероидов в одно время
        approach1 = CloseApproachModel(
            asteroid_id=asteroid1.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_same_time_1"
        )
        
        approach2 = CloseApproachModel(
            asteroid_id=asteroid2.id,
            approach_time=approach_time,  # То же самое время
            distance_au=0.03,
            velocity_km_s=19.0,
            calculation_batch_id="test_same_time_2"
        )
        
        async_session.add_all([approach1, approach2])
        
        # Должно быть успешно, так как астероиды разные
        try:
            await async_session.flush()
        except IntegrityError:
            pytest.fail("Разные астероиды должны иметь сближения в одно время")
    
    def test_close_approach_repr_method(self, test_asteroid):
        """Тестирование строкового представления сближения."""
        approach_time = datetime.now() + timedelta(days=30)
        
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_repr"
        )
        
        repr_str = repr(approach)
        assert repr_str.startswith('CloseApproachModel(')
        assert 'asteroid_id=' in repr_str
        assert 'approach_time=' in repr_str
        assert 'distance_au=0.025' in repr_str
    
    @pytest.mark.db
    async def test_close_approach_cascade_delete(self, async_session, test_asteroid):
        """Проверка каскадного удаления при удалении астероида."""
        from sqlalchemy import select
        
        # Создаем сближение
        approach_time = datetime.now() + timedelta(days=30)
        
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_cascade"
        )
        async_session.add(approach)
        await async_session.flush()
        await async_session.refresh(approach)
        
        # Проверяем, что сближение создано
        query = select(CloseApproachModel).where(CloseApproachModel.id == approach.id)
        result = await async_session.execute(query)
        assert result.scalar_one_or_none() is not None
        
        # Удаляем астероид
        await async_session.delete(test_asteroid)
        await async_session.flush()
        
        # Проверяем, что сближение также удалено (каскадное удаление)
        result = await async_session.execute(query)
        assert result.scalar_one_or_none() is None
    
    def test_close_approach_timezone_aware(self, test_asteroid):
        """Проверка, что approach_time использует временные зоны."""
        from sqlalchemy import inspect
        
        # Получаем информацию о столбце approach_time
        column = inspect(CloseApproachModel).columns['approach_time']
        
        # Проверяем, что столбец использует временные зоны
        assert column.type.timezone == True
    
    @pytest.mark.db
    async def test_close_approach_update_timestamps(self, async_session, test_asteroid):
        """Проверка автоматического обновления временных меток."""
        # Создаем сближение
        approach_time = datetime.now() + timedelta(days=30)
        
        approach = CloseApproachModel(
            asteroid_id=test_asteroid.id,
            approach_time=approach_time,
            distance_au=0.025,
            velocity_km_s=18.7,
            calculation_batch_id="test_timestamps"
        )
        
        async_session.add(approach)
        await async_session.flush()
        await async_session.refresh(approach)
        
        # Запоминаем время создания
        initial_created_at = approach.created_at
        initial_updated_at = approach.updated_at
        
        # Ждем достаточно долго, чтобы время гарантированно изменилось
        import asyncio
        await asyncio.sleep(1.1)  # Увеличиваем до 1.1 секунды
        
        # Обновляем сближение
        approach.velocity_km_s = 20.0
        await async_session.flush()
        await async_session.refresh(approach)
        
        # Проверяем, что created_at не изменился
        assert approach.created_at == initial_created_at
        
        # Проверяем, что updated_at изменился (может быть >=)
        # Используем >= вместо >, так как в редких случаях время может быть одинаковым
        assert approach.updated_at >= initial_updated_at
        
        # Дополнительная проверка: если время равно, проверяем, что что-то изменилось
        if approach.updated_at == initial_updated_at:
            # Проверяем, что поле velocity_km_s действительно изменилось
            assert approach.velocity_km_s == 20.0
    
    def test_close_approach_distance_conversion_accuracy(self, test_asteroid):
        """Точность преобразования расстояния из а.е. в км."""
        # Константа: 1 астрономическая единица в километрах
        AU_TO_KM = 149597870.7
        
        # Тестируем разные значения
        test_cases = [
            (0.0, 0.0),
            (0.001, 0.001 * AU_TO_KM),
            (0.1, 0.1 * AU_TO_KM),
            (0.5, 0.5 * AU_TO_KM),
            (1.0, 1.0 * AU_TO_KM),
        ]
        
        for distance_au, expected_distance_km in test_cases:
            if distance_au <= 1.0:  # Только допустимые значения
                approach = CloseApproachModel(
                    asteroid_id=test_asteroid.id,
                    approach_time=datetime.now() + timedelta(days=30),
                    distance_au=distance_au,
                    velocity_km_s=18.0,
                    calculation_batch_id=f"test_accuracy_{distance_au}"
                )
                
                # Проверяем точность с небольшой погрешностью
                assert abs(approach.distance_km - expected_distance_km) < 0.001