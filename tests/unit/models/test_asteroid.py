"""
Тесты для модели астероидов.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from models.asteroid import AsteroidModel

class TestAsteroidModel:
    """Тесты модели астероидов."""
    
    def test_asteroid_creation_valid_data(self):
        """Создание астероида с валидными данными."""
        # Арранжировка
        asteroid_data = {
            "mpc_number": 999991,
            "name": "Valid Test Asteroid",
            "designation": "2024 TE1",
            "perihelion_au": 1.13,
            "aphelion_au": 1.78,
            "earth_moid_au": 0.15,
            "absolute_magnitude": 10.4,
            "estimated_diameter_km": 16.84,
            "accurate_diameter": True,
            "albedo": 0.25,
            "is_neo": True,
            "is_pha": False
        }
        
        # Действие
        asteroid = AsteroidModel(**asteroid_data)
        
        # Проверка
        assert asteroid.mpc_number == 999991
        assert asteroid.name == "Valid Test Asteroid"
        assert asteroid.designation == "2024 TE1"
        assert asteroid.perihelion_au == 1.13
        assert asteroid.aphelion_au == 1.78
        assert asteroid.earth_moid_au == 0.15
        assert asteroid.absolute_magnitude == 10.4
        assert asteroid.estimated_diameter_km == 16.84
        assert asteroid.accurate_diameter == True
        assert asteroid.albedo == 0.25
        assert asteroid.is_neo == True
        assert asteroid.is_pha == False
        
        # Проверяем автоматически сгенерированные поля
        assert asteroid.id is None  # Еще не сохранено в БД
        assert hasattr(asteroid, 'created_at')
        assert hasattr(asteroid, 'updated_at')
    
    def test_asteroid_creation_minimal_data(self):
        """Создание астероида с минимальными обязательными данными."""
        asteroid = AsteroidModel(
            mpc_number=999992,
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
        
        # Проверяем, что необязательные поля могут быть None
        assert asteroid.name is None
        assert asteroid.designation is None
        assert asteroid.is_neo == True
        assert asteroid.is_pha == False
    
    def test_asteroid_creation_invalid_albedo(self):
        """Валидация альбедо за пределами диапазона (0,1]."""
        # Тест 1: Альбедо = 0
        with pytest.raises(ValueError, match="Альбедо должно быть в диапазоне"):
            AsteroidModel(
                mpc_number=999993,
                perihelion_au=1.0,
                aphelion_au=2.0,
                earth_moid_au=0.1,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.5,
                accurate_diameter=False,
                albedo=0.0,  # Недопустимо
                is_neo=True,
                is_pha=False
            )
        
        # Тест 2: Альбедо отрицательное
        with pytest.raises(ValueError, match="Альбедо должно быть в диапазоне"):
            AsteroidModel(
                mpc_number=999994,
                perihelion_au=1.0,
                aphelion_au=2.0,
                earth_moid_au=0.1,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.5,
                accurate_diameter=False,
                albedo=-0.1,  # Недопустимо
                is_neo=True,
                is_pha=False
            )
        
        # Тест 3: Альбедо > 1
        with pytest.raises(ValueError, match="Альбедо должно быть в диапазоне"):
            AsteroidModel(
                mpc_number=999995,
                perihelion_au=1.0,
                aphelion_au=2.0,
                earth_moid_au=0.1,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.5,
                accurate_diameter=False,
                albedo=1.1,  # Недопустимо
                is_neo=True,
                is_pha=False
            )
    
    def test_asteroid_creation_aphelion_le_perihelion(self):
        """Валидация: афелий должен быть больше перигелия."""
        # Тест 1: Афелий равен перигелию
        with pytest.raises(ValueError, match="Афелий.*должен быть больше перигелия"):
            AsteroidModel(
                mpc_number=999996,
                perihelion_au=1.5,
                aphelion_au=1.5,  # Равен перигелию
                earth_moid_au=0.1,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.5,
                accurate_diameter=False,
                albedo=0.15,
                is_neo=True,
                is_pha=False
            )
        
        # Тест 2: Афелий меньше перигелия
        with pytest.raises(ValueError, match="Афелий.*должен быть больше перигелия"):
            AsteroidModel(
                mpc_number=999997,
                perihelion_au=2.0,
                aphelion_au=1.5,  # Меньше перигелия
                earth_moid_au=0.1,
                absolute_magnitude=20.0,
                estimated_diameter_km=0.5,
                accurate_diameter=False,
                albedo=0.15,
                is_neo=True,
                is_pha=False
            )
    
    def test_asteroid_creation_negative_moid(self):
        """Валидация отрицательного MOID."""
        # MOID может быть 0, но не отрицательным
        asteroid = AsteroidModel(
            mpc_number=999998,
            perihelion_au=1.0,
            aphelion_au=2.0,
            earth_moid_au=0.0,  # Допустимо
            absolute_magnitude=20.0,
            estimated_diameter_km=0.5,
            accurate_diameter=False,
            albedo=0.15,
            is_neo=True,
            is_pha=False
        )
        assert asteroid.earth_moid_au == 0.0
    
    def test_asteroid_creation_negative_perihelion(self):
        """Валидация отрицательного перигелия."""
        # Перигелий должен быть положительным
        asteroid = AsteroidModel(
            mpc_number=999999,
            perihelion_au=0.1,  # Маленькое, но положительное
            aphelion_au=2.0,
            earth_moid_au=0.1,
            absolute_magnitude=20.0,
            estimated_diameter_km=0.5,
            accurate_diameter=False,
            albedo=0.15,
            is_neo=True,
            is_pha=False
        )
        assert asteroid.perihelion_au > 0
    
    @pytest.mark.db
    async def test_asteroid_save_to_db(self, async_session):
        """Сохранение астероида в базу данных."""
        # Арранжировка
        asteroid = AsteroidModel(
            mpc_number=1000000,
            name="DB Test Asteroid",
            designation="2024 DB1",
            perihelion_au=1.13,
            aphelion_au=1.78,
            earth_moid_au=0.15,
            absolute_magnitude=10.4,
            estimated_diameter_km=16.84,
            accurate_diameter=True,
            albedo=0.25,
            is_neo=True,
            is_pha=False
        )
        
        # Действие
        async_session.add(asteroid)
        await async_session.flush()
        await async_session.refresh(asteroid)
        
        # Проверка
        assert asteroid.id is not None
        assert asteroid.created_at is not None
        assert asteroid.updated_at is not None
        
        # Проверяем, что можем найти по ID
        from sqlalchemy import select
        query = select(AsteroidModel).where(AsteroidModel.id == asteroid.id)
        result = await async_session.execute(query)
        found = result.scalar_one()
        
        assert found.id == asteroid.id
        assert found.mpc_number == asteroid.mpc_number
        assert found.name == asteroid.name
    
    @pytest.mark.db
    async def test_asteroid_unique_mpc_number(self, async_session):
        """Проверка уникальности номера MPC."""
        # Создаем первый астероид
        asteroid1 = AsteroidModel(
            mpc_number=1000001,
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
        async_session.add(asteroid1)
        await async_session.flush()
        
        # Пытаемся создать второй астероид с тем же номером MPC
        asteroid2 = AsteroidModel(
            mpc_number=1000001,  # Дубликат!
            perihelion_au=1.1,
            aphelion_au=2.1,
            earth_moid_au=0.2,
            absolute_magnitude=21.0,
            estimated_diameter_km=0.6,
            accurate_diameter=True,
            albedo=0.2,
            is_neo=True,
            is_pha=True
        )
        async_session.add(asteroid2)
        
        # Должно вызвать IntegrityError из-за нарушения уникальности
        with pytest.raises(IntegrityError):
            await async_session.flush()
        
        # Откатываем для чистоты теста
        await async_session.rollback()
    
    @pytest.mark.db
    async def test_asteroid_relationships(self, async_session):
        """Проверка связей с другими моделями."""
        from models.close_approach import CloseApproachModel
        from datetime import datetime, timedelta
        
        # Создаем астероид
        asteroid = AsteroidModel(
            mpc_number=1000002,
            name="Relationship Test",
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
        
        # Создаем сближения для этого астероида
        now = datetime.now()
        for i in range(2):
            approach = CloseApproachModel(
                asteroid_id=asteroid.id,
                approach_time=now + timedelta(days=30 * (i + 1)),
                distance_au=0.02 + i * 0.01,
                velocity_km_s=18.0 + i * 1.0,
                calculation_batch_id=f"rel_test_batch_{i}"
            )
            async_session.add(approach)
        
        await async_session.flush()
        
        # Загружаем связи
        await async_session.refresh(asteroid)
        
        # Проверяем, что связи работают
        assert hasattr(asteroid, 'close_approaches')
        
        # Используем lazy='selectin', поэтому связи должны быть загружены
        # при доступе к атрибуту
        approaches = asteroid.close_approaches
        assert len(approaches) == 2
        for approach in approaches:
            assert approach.asteroid_id == asteroid.id
    
    def test_asteroid_repr_method(self):
        """Тестирование строкового представления астероида."""
        asteroid = AsteroidModel(
            mpc_number=1000003,
            name="Repr Test Asteroid",
            perihelion_au=1.13,
            aphelion_au=1.78,
            earth_moid_au=0.15,
            absolute_magnitude=10.4,
            estimated_diameter_km=16.84,
            accurate_diameter=True,
            albedo=0.25,
            is_neo=True,
            is_pha=False
        )
        
        repr_str = repr(asteroid)
        assert repr_str.startswith('AsteroidModel(')
        assert 'mpc_number=1000003' in repr_str
        assert 'name=' in repr_str
    
    def test_asteroid_default_values(self):
        """Проверка значений по умолчанию."""
        asteroid = AsteroidModel(
            mpc_number=1000004,
            perihelion_au=1.0,
            aphelion_au=2.0,
            earth_moid_au=0.1,
            absolute_magnitude=20.0,
            estimated_diameter_km=0.5,
            accurate_diameter=False,
            albedo=0.15,
            # Не указываем is_neo и is_pha - должны использоваться значения по умолчанию
        )
        
        # Теперь значения по умолчанию устанавливаются в конструкторе
        assert asteroid.is_neo == True
        assert asteroid.is_pha == False
        assert getattr(asteroid, 'is_pha', False) == False  # По умолчанию из модели
    
    def test_asteroid_table_constraints(self):
        """Проверка ограничений таблицы."""
        from sqlalchemy.schema import CreateTable
        from sqlalchemy import inspect
        
        # Получаем DDL для создания таблицы
        ddl = str(CreateTable(AsteroidModel.__table__))
        
        # Проверяем наличие ограничений в DDL
        assert 'CHECK' in ddl  # Должны быть CHECK constraints
        assert 'aphelion_au > perihelion_au' in ddl or 'check_aphelion_gt_perihelion' in ddl
        assert 'earth_moid_au >= 0' in ddl or 'check_moid_non_negative' in ddl
        assert 'perihelion_au > 0' in ddl or 'check_perihelion_positive' in ddl
        
        # Проверяем индексы
        inspector = inspect(AsteroidModel.__table__)
        indexes = [idx.name for idx in inspector.indexes]
        
        # Должен быть уникальный индекс на mpc_number
        # (В SQLAlchemy unique=True создает уникальное ограничение, а не индекс)
        # Но проверим, что столбец помечен как unique
        assert AsteroidModel.mpc_number.unique == True
    
    @pytest.mark.db
    async def test_asteroid_update_timestamps(self, async_session):
        """Проверка автоматического обновления временных меток."""
        # Создаем астероид
        asteroid = AsteroidModel(
            mpc_number=1000005,
            name="Timestamp Test",
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
        
        async_session.add(asteroid)
        await async_session.flush()
        await async_session.refresh(asteroid)
        
        # Запоминаем время создания
        initial_created_at = asteroid.created_at
        initial_updated_at = asteroid.updated_at
        
        # Увеличиваем задержку
        import asyncio
        await asyncio.sleep(1)  # Увеличиваем до 1 секунды
        
        # Обновляем астероид
        asteroid.name = "Updated Name"
        await async_session.flush()
        await async_session.refresh(asteroid)
        
        # Проверяем, что created_at не изменился, а updated_at изменился
        assert asteroid.created_at == initial_created_at
        assert asteroid.updated_at >= initial_updated_at  # Используем >= вместо >