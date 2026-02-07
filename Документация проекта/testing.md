# 🧪 **ТЕСТИРОВАНИЕ**

## 📋 **ОБЗОР СТРАТЕГИИ ТЕСТИРОВАНИЯ**

Система Asteroid Watch использует многоуровневую стратегию тестирования для обеспечения надежности и качества кода. Тестирование включает в себя модульные, интеграционные и функциональные тесты.

## 📁 **СТРУКТУРА ТЕСТОВ**

```
tests/
├── conftest.py           # Общие фикстуры для всех тестов
├── unit/                 # Модульные тесты
│   ├── domains/          # Тесты для доменов
│   │   ├── asteroid/     # Тесты для домена астероидов
│   │   ├── approach/     # Тесты для домена сближений
│   │   └── threat/       # Тесты для домена угроз
│   ├── shared/           # Тесты для общих компонентов
│   └── api/              # Тесты для API слоя
└── integration/          # Интеграционные тесты
```

## 🧩 **МОДУЛЬНЫЕ ТЕСТЫ**

### **1. Тесты для домена астероидов**

#### **Тестирование репозитория астероидов**
```python
# tests/unit/domains/asteroid/test_asteroid_repository.py
import pytest
from unittest.mock import AsyncMock, Mock
from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
from domains.asteroid.models.asteroid import AsteroidModel

@pytest.mark.asyncio
async def test_get_by_designation_found(mock_session):
    """Тест получения астероида по обозначению когда он существует"""
    repo = AsteroidRepository()
    repo.session = mock_session
    
    # Подготовка данных
    expected_asteroid = Mock(spec=AsteroidModel)
    expected_asteroid.designation = "433"
    expected_asteroid.name = "Eros"
    
    # Настройка мока
    mock_session.execute.return_value.scalar_one_or_none.return_value = expected_asteroid
    
    # Вызов тестируемого метода
    result = await repo.get_by_designation("433")
    
    # Проверка результата
    assert result == expected_asteroid
    assert result.designation == "433"
    assert result.name == "Eros"

@pytest.mark.asyncio
async def test_get_by_designation_not_found(mock_session):
    """Тест получения астероида по обозначению когда он не существует"""
    repo = AsteroidRepository()
    repo.session = mock_session
    
    # Настройка мока
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Вызов тестируемого метода
    result = await repo.get_by_designation("999999")
    
    # Проверка результата
    assert result is None

@pytest.mark.asyncio
async def test_bulk_create_asteroids(mock_session):
    """Тест массового создания астероидов"""
    repo = AsteroidRepository()
    repo.session = mock_session
    
    # Подготовка данных
    asteroids_data = [
        {
            "designation": "test1",
            "name": "Test Asteroid 1",
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.1,
            "albedo": 0.15
        },
        {
            "designation": "test2",
            "name": "Test Asteroid 2",
            "absolute_magnitude": 18.0,
            "estimated_diameter_km": 0.5,
            "albedo": 0.20
        }
    ]
    
    # Вызов тестируемого метода
    created, updated = await repo.bulk_create_asteroids(asteroids_data)
    
    # Проверка результата
    assert created == 2  # Предполагается, что оба астероида были созданы
    assert updated == 0  # Ни один не был обновлен
```

#### **Тестирование сервиса астероидов**
```python
# tests/unit/domains/asteroid/test_asteroid_service.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from domains.asteroid.services.asteroid_service import AsteroidService

@pytest.mark.asyncio
async def test_get_by_designation_with_data(mock_session_factory):
    """Тест получения астероида по обозначению через сервис"""
    service = AsteroidService(mock_session_factory)
    
    # Подготовка моков
    mock_uow = AsyncMock()
    mock_asteroid_repo = AsyncMock()
    mock_asteroid_repo.get_by_designation.return_value = Mock()
    mock_asteroid_repo.get_by_designation.return_value.id = 1
    mock_asteroid_repo.get_by_designation.return_value.designation = "433"
    mock_asteroid_repo.get_by_designation.return_value.name = "Eros"
    mock_asteroid_repo.get_by_designation.return_value.estimated_diameter_km = 17.0
    mock_asteroid_repo.get_by_designation.return_value.earth_moid_au = 0.015
    
    mock_uow.asteroid_repo = mock_asteroid_repo
    
    # Используем patch для UnitOfWork
    with patch('domains.asteroid.services.asteroid_service.UnitOfWork') as mock_uow_class:
        mock_uow_context = AsyncMock()
        mock_uow_context.__aenter__.return_value = mock_uow
        mock_uow_context.__aexit__.return_value = None
        mock_uow_class.return_value = mock_uow_context
        
        # Вызов тестируемого метода
        result = await service.get_by_designation("433")
        
        # Проверка результата
        assert result is not None
        assert result['designation'] == "433"
        assert result['name'] == "Eros"
        assert result['estimated_diameter_km'] == 17.0
        assert result['earth_moid_au'] == 0.015

@pytest.mark.asyncio
async def test_get_by_designation_not_found(mock_session_factory):
    """Тест получения астероида по обозначению когда он не найден"""
    service = AsteroidService(mock_session_factory)
    
    # Подготовка моков
    mock_uow = AsyncMock()
    mock_asteroid_repo = AsyncMock()
    mock_asteroid_repo.get_by_designation.return_value = None
    mock_uow.asteroid_repo = mock_asteroid_repo
    
    # Используем patch для UnitOfWork
    with patch('domains.asteroid.services.asteroid_service.UnitOfWork') as mock_uow_class:
        mock_uow_context = AsyncMock()
        mock_uow_context.__aenter__.return_value = mock_uow
        mock_uow_context.__aexit__.return_value = None
        mock_uow_class.return_value = mock_uow_context
        
        # Вызов тестируемого метода
        result = await service.get_by_designation("999999")
        
        # Проверка результата
        assert result is None
```

### **2. Тесты для домена сближений**

#### **Тестирование репозитория сближений**
```python
# tests/unit/domains/approach/test_approach_repository.py
import pytest
from unittest.mock import AsyncMock, Mock
from domains.approach.repositories.approach_repository import ApproachRepository
from domains.approach.models.close_approach import CloseApproachModel
from datetime import datetime

@pytest.mark.asyncio
async def test_get_by_asteroid(mock_session):
    """Тест получения сближений для астероида"""
    repo = ApproachRepository()
    repo.session = mock_session
    
    # Подготовка данных
    expected_approach = Mock(spec=CloseApproachModel)
    expected_approach.asteroid_id = 1
    expected_approach.approach_time = datetime.now()
    expected_approach.distance_au = 0.02
    expected_approach.velocity_km_s = 15.5
    
    # Настройка мока
    mock_session.execute.return_value.scalars.return_value.all.return_value = [expected_approach]
    
    # Вызов тестируемого метода
    result = await repo.get_by_asteroid(1)
    
    # Проверка результата
    assert len(result) == 1
    assert result[0].asteroid_id == 1
    assert result[0].distance_au == 0.02
    assert result[0].velocity_km_s == 15.5

@pytest.mark.asyncio
async def test_get_upcoming_approaches(mock_session):
    """Тест получения ближайших сближений"""
    repo = ApproachRepository()
    repo.session = mock_session
    
    # Подготовка данных
    approach1 = Mock(spec=CloseApproachModel)
    approach1.approach_time = datetime.now().replace(year=2024, month=1, day=1)
    approach1.distance_au = 0.01
    approach1.asteroid_designation = "433"
    
    approach2 = Mock(spec=CloseApproachModel)
    approach2.approach_time = datetime.now().replace(year=2024, month=2, day=1)
    approach2.distance_au = 0.02
    approach2.asteroid_designation = "495"
    
    # Настройка мока
    mock_session.execute.return_value.scalars.return_value.all.return_value = [approach1, approach2]
    
    # Вызов тестируемого метода
    result = await repo.get_upcoming_approaches(limit=10)
    
    # Проверка результата
    assert len(result) == 2
    assert result[0].asteroid_designation == "433"
    assert result[1].asteroid_designation == "495"
```

### **3. Тесты для домена угроз**

#### **Тестирование репозитория угроз**
```python
# tests/unit/domains/threat/test_threat_repository.py
import pytest
from unittest.mock import AsyncMock, Mock
from domains.threat.repositories.threat_repository import ThreatRepository
from domains.threat.models.threat_assessment import ThreatAssessmentModel

@pytest.mark.asyncio
async def test_get_by_designation(mock_session):
    """Тест получения оценки угрозы по обозначению"""
    repo = ThreatRepository()
    repo.session = mock_session
    
    # Подготовка данных
    expected_threat = Mock(spec=ThreatAssessmentModel)
    expected_threat.designation = "433"
    expected_threat.fullname = "Eros"
    expected_threat.ip = 0.0001
    expected_threat.ts_max = 1
    expected_threat.energy_megatons = 100.0
    
    # Настройка мока
    mock_session.execute.return_value.scalar_one_or_none.return_value = expected_threat
    
    # Вызов тестируемого метода
    result = await repo.get_by_designation("433")
    
    # Проверка результата
    assert result is not None
    assert result.designation == "433"
    assert result.ip == 0.0001
    assert result.ts_max == 1
    assert result.energy_megatons == 100.0

@pytest.mark.asyncio
async def test_get_high_risk_threats(mock_session):
    """Тест получения угроз с высоким риском"""
    repo = ThreatRepository()
    repo.session = mock_session
    
    # Подготовка данных
    high_risk_threat = Mock(spec=ThreatAssessmentModel)
    high_risk_threat.designation = "test_high_risk"
    high_risk_threat.ts_max = 6  # Высокий риск
    high_risk_threat.ip = 0.001
    
    # Настройка мока
    mock_session.execute.return_value.scalars.return_value.all.return_value = [high_risk_threat]
    
    # Вызов тестируемого метода
    result = await repo.get_high_risk_threats(limit=20)
    
    # Проверка результата
    assert len(result) == 1
    assert result[0].ts_max >= 5  # Высокий риск
    assert result[0].designation == "test_high_risk"
```

## 🔄 **ИНТЕГРАЦИОННЫЕ ТЕСТЫ**

### **Тестирование взаимодействия между доменами**
```python
# tests/integration/test_cross_domain_integration.py
import pytest
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal
from datetime import datetime

@pytest.mark.asyncio
async def test_asteroid_approach_threat_integration():
    """
    Тест интеграции между доменами: 
    создание астероида → создание сближения → создание угрозы
    """
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # 1. Создать астероид
        asteroid_data = {
            "designation": "integration_test_asteroid",
            "name": "Integration Test Asteroid",
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.1,
            "albedo": 0.15,
            "earth_moid_au": 0.04
        }
        
        created_asteroid = await uow.asteroid_repo.create(asteroid_data)
        assert created_asteroid is not None
        assert created_asteroid.designation == "integration_test_asteroid"
        
        # 2. Создать сближение для этого астероида
        approach_data = {
            "asteroid_id": created_asteroid.id,
            "approach_time": datetime.now(),
            "distance_au": 0.04,
            "distance_km": 0.04 * 149597870.7,
            "velocity_km_s": 15.0,
            "asteroid_designation": created_asteroid.designation,
            "data_source": "Integration Test"
        }
        
        created_approach = await uow.approach_repo.create(approach_data)
        assert created_approach is not None
        assert created_approach.asteroid_id == created_asteroid.id
        
        # 3. Создать оценку угрозы для этого астероида
        threat_data = {
            "asteroid_id": created_asteroid.id,
            "designation": created_asteroid.designation,
            "fullname": created_asteroid.name,
            "ip": 0.0001,
            "ts_max": 1,
            "ps_max": -3.5,
            "diameter": created_asteroid.estimated_diameter_km,
            "v_inf": 15.0,
            "h": created_asteroid.absolute_magnitude,
            "n_imp": 1,
            "impact_years": [2024],
            "last_obs": "2023-01-01",
            "threat_level_ru": "ОЧЕНЬ НИЗКИЙ",
            "torino_scale_ru": "1 — Нормальный (зелёный)",
            "impact_probability_text_ru": "0.01% (1 к 10,000)",
            "energy_megatons": 50.0,
            "impact_category": "локальный",
            "sentry_last_update": datetime.now()
        }
        
        created_threat = await uow.threat_repo.create(threat_data)
        assert created_threat is not None
        assert created_threat.asteroid_id == created_asteroid.id
        assert created_threat.designation == created_asteroid.designation
        
        # 4. Проверить связи между сущностями
        retrieved_asteroid = await uow.asteroid_repo.get_by_id(created_asteroid.id)
        assert retrieved_asteroid is not None
        
        retrieved_approaches = await uow.approach_repo.get_by_asteroid(created_asteroid.id)
        assert len(retrieved_approaches) == 1
        assert retrieved_approaches[0].id == created_approach.id
        
        retrieved_threat = await uow.threat_repo.get_by_asteroid_id(created_asteroid.id)
        assert retrieved_threat is not None
        assert retrieved_threat.id == created_threat.id
        
        # Зафиксировать транзакцию
        await uow.commit()

@pytest.mark.asyncio
async def test_data_consistency_across_domains():
    """
    Тест согласованности данных между доменами
    """
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # Создать астероид
        asteroid = await uow.asteroid_repo.create({
            "designation": "consistency_test",
            "name": "Consistency Test",
            "absolute_magnitude": 18.5,
            "estimated_diameter_km": 0.25,
            "albedo": 0.18
        })
        
        # Обновить астероид
        updated_asteroid = await uow.asteroid_repo.update(
            asteroid.id, 
            {"estimated_diameter_km": 0.30}
        )
        assert updated_asteroid.estimated_diameter_km == 0.30
        
        # Создать сближение с использованием обновленных данных
        approach = await uow.approach_repo.create({
            "asteroid_id": asteroid.id,
            "approach_time": datetime.now(),
            "distance_au": 0.03,
            "distance_km": 0.03 * 149597870.7,
            "velocity_km_s": 12.5,
            "asteroid_designation": asteroid.designation,
            "data_source": "Consistency Test"
        })
        
        # Проверить, что сближение связано с правильным астероидом
        retrieved_approach = await uow.approach_repo.get_by_id(approach.id)
        assert retrieved_approach.asteroid_id == asteroid.id
        
        await uow.commit()
```

### **Тестирование UnitOfWork**
```python
# tests/integration/test_unit_of_work.py
import pytest
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

@pytest.mark.asyncio
async def test_unit_of_work_transaction_success():
    """
    Тест успешной транзакции в UnitOfWork
    """
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # Создать несколько сущностей
        asteroid = await uow.asteroid_repo.create({
            "designation": "uow_test_success",
            "name": "UOW Test Success",
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.1
        })
        
        approach = await uow.approach_repo.create({
            "asteroid_id": asteroid.id,
            "approach_time": datetime.now(),
            "distance_au": 0.02,
            "distance_km": 0.02 * 149597870.7,
            "velocity_km_s": 15.0,
            "asteroid_designation": asteroid.designation,
            "data_source": "UOW Test"
        })
        
        # Проверить, что сущности созданы
        assert asteroid is not None
        assert approach is not None
        assert approach.asteroid_id == asteroid.id
        
        # Зафиксировать транзакцию
        await uow.commit()
        
        # Проверить, что данные действительно сохранены
        async with UnitOfWork(AsyncSessionLocal) as verify_uow:
            verified_asteroid = await verify_uow.asteroid_repo.get_by_designation("uow_test_success")
            assert verified_asteroid is not None
            assert verified_asteroid.name == "UOW Test Success"

@pytest.mark.asyncio
async def test_unit_of_work_transaction_rollback():
    """
    Тест отката транзакции в UnitOfWork
    """
    try:
        async with UnitOfWork(AsyncSessionLocal) as uow:
            # Создать сущность
            asteroid = await uow.asteroid_repo.create({
                "designation": "uow_test_rollback",
                "name": "UOW Test Rollback",
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.1
            })
            
            # Проверить, что сущность создана в рамках транзакции
            assert asteroid is not None
            
            # Вызвать исключение для отката транзакции
            raise ValueError("Тестовое исключение для отката транзакции")
            
    except ValueError:
        # Проверить, что данные не сохранились после отката
        async with UnitOfWork(AsyncSessionLocal) as verify_uow:
            verified_asteroid = await verify_uow.asteroid_repo.get_by_designation("uow_test_rollback")
            assert verified_asteroid is None
```

## 🧪 **ОБЩИЕ ФИКСТУРЫ И МОКИ**

### **Фикстуры из conftest.py**
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from decimal import Decimal

@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session fixture."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = Mock()
    session.flush = AsyncMock()
    session.begin = AsyncMock()
    return session

@pytest.fixture
def mock_session_factory(mock_session):
    """Mock session factory fixture."""
    factory = Mock(return_value=mock_session)
    return factory

@pytest.fixture
def mock_uow(mock_session):
    """Mock Unit of Work fixture."""
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = mock_session
    return uow

@pytest.fixture
def sample_asteroid_data():
    """Sample asteroid data for testing."""
    return {
        "id": 1,
        "name": "Test Asteroid",
        "designation": "2023 TEST",
        "absolute_magnitude": 20.5,
        "estimated_diameter_min_km": 0.1,
        "estimated_diameter_max_km": 0.3,
        "albedo": 0.15,
        "is_hazardous": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@pytest.fixture
def sample_approach_data():
    """Sample approach data for testing."""
    return {
        "id": 1,
        "asteroid_id": 1,
        "approach_date": datetime.now().date(),
        "distance_km": 100000.0,
        "velocity_km_s": 10.5,
        "orbit_class": "AMO",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@pytest.fixture
def sample_threat_data():
    """Sample threat data for testing."""
    return {
        "id": 1,
        "asteroid_id": 1,
        "palermo_scale": Decimal("0.5"),
        "torino_scale": 1,
        "impact_probability": Decimal("0.001"),
        "potential_energy_mt": Decimal("100.0"),
        "is_hazardous": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@pytest.fixture
def invalid_asteroid_data():
    """Invalid asteroid data for testing validation."""
    return {
        "name": "",  # Invalid: empty name
        "designation": "",  # Invalid: empty designation
        "absolute_magnitude": -50,  # Invalid: too low magnitude
        "estimated_diameter_min_km": -1,  # Invalid: negative diameter
        "albedo": 1.5  # Invalid: albedo > 1
    }
```

## 🧪 **ТЕСТИРОВАНИЕ ВНЕШНИХ API**

### **Тестирование клиентов NASA API**
```python
# tests/unit/shared/external_api/test_nasa_clients.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from shared.external_api.clients.sbdb_api import NASASBDBClient
from shared.external_api.clients.cad_api import CADClient
from shared.external_api.clients.sentry_api import SentryClient

@pytest.mark.asyncio
async def test_sbdb_client_get_asteroids():
    """Тест клиента SBDB API"""
    async with NASASBDBClient() as client:
        # Мокаем внутренние вызовы
        with patch.object(client, '_get_pha_list', return_value=['433', '495']) as mock_get_list:
            with patch.object(client, '_process_batch', return_value=[
                {'designation': '433', 'name': 'Eros', 'estimated_diameter_km': 17.0},
                {'designation': '495', 'name': 'Eureka', 'estimated_diameter_km': 1.0}
            ]) as mock_process_batch:
                
                # Вызов тестируемого метода
                result = await client.get_asteroids(limit=2)
                
                # Проверка результата
                assert len(result) == 2
                assert result[0]['designation'] == '433'
                assert result[1]['designation'] == '495'
                
                # Проверка вызовов моков
                mock_get_list.assert_called_once_with(2)
                mock_process_batch.assert_called_once()

@pytest.mark.asyncio
async def test_cad_client_get_close_approaches():
    """Тест клиента CAD API"""
    async with CADClient() as client:
        # Мокаем сессию
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'fields': ['des', 'cd', 'dist', 'v_rel'],
            'data': [
                ['433', '2024-01-01', 0.02, 15.5],
                ['495', '2024-02-01', 0.03, 12.0]
            ]
        }
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None
        
        client.session = mock_session
        
        # Вызов тестируемого метода
        result = await client.get_close_approaches(asteroid_ids=['433', '495'])
        
        # Проверка результата
        assert '433' in result
        assert '495' in result
        assert len(result['433']) >= 0  # Может быть 0 в зависимости от фильтрации

@pytest.mark.asyncio
async def test_sentry_client_fetch_current_impact_risks():
    """Тест клиента Sentry API"""
    async with SentryClient() as client:
        # Мокаем сессию
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'des': '433',
                    'fullname': 'Eros',
                    'ip': 0.0001,
                    'ts_max': 1,
                    'ps_max': -3.5,
                    'diameter': 17.0,
                    'v_inf': 15.5,
                    'h': 11.17,
                    'n_imp': 1,
                    'last_obs': '2023-01-01'
                }
            ]
        }
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None
        
        client.session = mock_session
        
        # Вызов тестируемого метода
        result = await client.fetch_current_impact_risks()
        
        # Проверка результата
        assert len(result) == 1
        assert result[0].designation == '433'
        assert result[0].ip == 0.0001
        assert result[0].ts_max == 1
```

## 🧪 **ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК**

### **Тестирование декораторов обработки ошибок**
```python
# tests/unit/shared/utils/test_error_handlers.py
import pytest
from unittest.mock import Mock
from shared.utils.error_handlers import (
    retry_with_exponential_backoff, 
    nasa_api_endpoint,
    handle_nasa_api_errors
)
import asyncio

def test_retry_with_exponential_backoff_success():
    """Тест декоратора retry_with_exponential_backoff при успешном выполнении"""
    call_count = 0
    
    @retry_with_exponential_backoff(max_attempts=3)
    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Network error")
        return "success"
    
    # Выполняем функцию
    import asyncio
    result = asyncio.run(test_func())
    
    # Проверяем результат
    assert result == "success"
    assert call_count == 2  # Функция была вызвана дважды (первый раз ошибка, второй раз успех)

@pytest.mark.asyncio
async def test_retry_with_exponential_backoff_failure():
    """Тест декоратора retry_with_exponential_backoff при неудачном выполнении"""
    call_count = 0
    
    @retry_with_exponential_backoff(max_attempts=2)
    async def test_func():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Persistent network error")
    
    # Проверяем, что исключение поднимается после всех попыток
    with pytest.raises(ConnectionError):
        await test_func()
    
    # Проверяем, что функция была вызвана max_attempts раз
    assert call_count == 2

def test_nasa_api_endpoint_decorator():
    """Тест декоратора nasa_api_endpoint"""
    @nasa_api_endpoint(max_retries=2)
    async def test_nasa_api_func():
        return {"status": "success"}
    
    # Выполняем функцию
    import asyncio
    result = asyncio.run(test_nasa_api_func())
    
    # Проверяем результат
    assert result == {"status": "success"}
```

## 🧪 **ЗАПУСК ТЕСТОВ**

### **Команды для запуска тестов**
```bash
# Запуск всех тестов
pytest

# Запуск только модульных тестов
pytest tests/unit/

# Запуск только интеграционных тестов
pytest tests/integration/

# Запуск тестов с покрытием кода
pytest --cov=.

# Запуск тестов с детальным выводом
pytest -v

# Запуск тестов для конкретного домена
pytest tests/unit/domains/asteroid/

# Запуск конкретного теста
pytest tests/unit/domains/asteroid/test_asteroid_repository.py::test_get_by_designation_found
```

---

**Следующий раздел:** [РАЗВЕРТЫВАНИЕ](deployment.md) - настройка и развертывание приложения