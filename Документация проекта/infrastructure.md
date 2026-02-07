# 🏗️ **ИНФРАСТРУКТУРА**

## 📋 **ОБЗОР**

Инфраструктурные компоненты (`shared/infrastructure/`) содержат базовые классы и интерфейсы, которые обеспечивают общую функциональность для всех доменов. Это включает базовые репозитории, схемы, и другие общие компоненты.

## 📐 **БАЗОВЫЕ СХЕМЫ (schemas)**

### **BaseSchema**
**Расположение:** `shared/infrastructure/schemas/base_schema.py`

**Назначение:** Базовая Pydantic схема с общими полями, которые присутствуют во всех моделях.

**Атрибуты:**
- `id` (int): Уникальный идентификатор
- `created_at` (datetime): Время создания
- `updated_at` (datetime): Время обновления

**Пример использования:**
```python
from shared.infrastructure import BaseSchema

class MyCustomSchema(BaseSchema):
    name: str
    value: float
```

### **CreateSchema**
**Назначение:** Базовая Pydantic схема для создания новых записей.

**Пример использования:**
```python
from shared.infrastructure import CreateSchema

class AsteroidCreateSchema(CreateSchema):
    designation: str
    name: Optional[str] = None
    absolute_magnitude: float
```

## 🏪 **БАЗОВЫЙ РЕПОЗИТОРИЙ (repositories)**

### **BaseRepository**
**Расположение:** `shared/infrastructure/repositories/base_repository.py`

**Назначение:** Базовый класс репозитория с оптимизированными CRUD-операциями, который наследуют все специализированные репозитории.

**Атрибуты:**
- `model`: Класс модели SQLAlchemy
- `_session`: Сессия базы данных
- `_model_columns`: Кешированные колонки модели
- `_model_column_types`: Кешированные типы колонок модели

**Методы:**

#### **`__init__(model: Type[ModelType])`**
- **Назначение:** Инициализирует репозиторий с указанной моделью

#### **`create(data: Dict[str, Any]) -> ModelType`**
- **Назначение:** Создает новую запись в базе данных и выполняет коммит
- **Параметры:** `data` - данные для создания
- **Возвращает:** `ModelType` - созданный экземпляр модели
- **Пример:**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async with UnitOfWork(AsyncSessionLocal) as uow:
    new_asteroid = await uow.asteroid_repo.create({
        "designation": "test_asteroid",
        "name": "Test Asteroid",
        "absolute_magnitude": 20.0,
        "estimated_diameter_km": 0.1,
        "albedo": 0.15
    })
    print(f"Создан астероид с ID: {new_asteroid.id}")
```

#### **`get_by_id(id: int) -> Optional[ModelType]`**
- **Назначение:** Получает запись по её ID. Без коммита (чтение)
- **Параметры:** `id` - ID записи
- **Возвращает:** `Optional[ModelType]` - экземпляр модели или None
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    asteroid = await uow.asteroid_repo.get_by_id(123)
    if asteroid:
        print(f"Найден астероид: {asteroid.name}")
```

#### **`update(id: int, update_data: Dict[str, Any]) -> Optional[ModelType]`**
- **Назначение:** Обновляет запись по ID и выполняет коммит
- **Параметры:** `id` - ID записи, `update_data` - данные для обновления
- **Возвращает:** `Optional[ModelType]` - обновленный экземпляр модели или None
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    updated_asteroid = await uow.asteroid_repo.update(123, {
        "estimated_diameter_km": 2.5
    })
    if updated_asteroid:
        print(f"Астероид обновлен: {updated_asteroid.estimated_diameter_km} км")
```

#### **`delete(id: int) -> bool`**
- **Назначение:** Удаляет запись по ID и выполняет коммит
- **Параметры:** `id` - ID записи
- **Возвращает:** `bool` - успешность удаления
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    success = await uow.asteroid_repo.delete(123)
    if success:
        print("Астероид удален успешно")
```

#### **`get_all(skip: int = 0, limit: Optional[int] = 100) -> List[ModelType]`**
- **Назначение:** Получает все записи с пагинацией. Без коммита (чтение)
- **Параметры:** `skip`, `limit`
- **Возвращает:** `List[ModelType]` - список записей
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    asteroids = await uow.asteroid_repo.get_all(skip=0, limit=10)
    print(f"Получено {len(asteroids)} астероидов")
```

#### **`count() -> int`**
- **Назначение:** Подсчитывает общее количество записей. Без коммита (чтение)
- **Возвращает:** `int` - количество записей
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    total = await uow.asteroid_repo.count()
    print(f"Всего астероидов: {total}")
```

#### **`filter(filters: Dict[str, Any], skip: int = 0, limit: Optional[int] = 100, order_by: Optional[str] = None, order_desc: bool = False) -> List[ModelType]`**
- **Назначение:** Универсальный метод фильтрации записей. Без коммита (чтение)
- **Параметры:** `filters`, `skip`, `limit`, `order_by`, `order_desc`
- **Возвращает:** `List[ModelType]` - список записей, соответствующих фильтрам
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    # Найти астероиды с диаметром больше 1 км
    large_asteroids = await uow.asteroid_repo.filter(
        filters={"estimated_diameter_km__ge": 1.0},
        skip=0,
        limit=10,
        order_by="estimated_diameter_km",
        order_desc=True
    )
    print(f"Найдено крупных астероидов: {len(large_asteroids)}")
```

#### **`bulk_create(data_list: List[Dict[str, Any]], conflict_action: str = "update", conflict_fields: Optional[List[str]] = None) -> Tuple[int, int]`**
- **Назначение:** Оптимизированное массовое создание записей с коммитом
- **Параметры:** `data_list`, `conflict_action`, `conflict_fields`
- **Возвращает:** `Tuple[int, int]` - количество созданных и обновленных записей
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    data_list = [
        {"designation": "test1", "name": "Test 1", "absolute_magnitude": 20.0, "estimated_diameter_km": 0.1, "albedo": 0.15},
        {"designation": "test2", "name": "Test 2", "absolute_magnitude": 18.0, "estimated_diameter_km": 0.5, "albedo": 0.2}
    ]
    created, updated = await uow.asteroid_repo.bulk_create(data_list)
    print(f"Создано: {created}, Обновлено: {updated}")
```

#### **`search(search_term: str, search_fields: List[str], skip: int = 0, limit: Optional[int] = 50) -> List[ModelType]`**
- **Назначение:** Поиск по нескольким текстовым полям. Без коммита (чтение)
- **Параметры:** `search_term`, `search_fields`, `skip`, `limit`
- **Возвращает:** `List[ModelType]` - список найденных записей
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    results = await uow.asteroid_repo.search(
        search_term="apophis",
        search_fields=["name", "designation"],
        skip=0,
        limit=10
    )
    print(f"Найдено {len(results)} результатов")
```

#### **`bulk_delete(filters: Dict[str, Any]) -> int`**
- **Назначение:** Массовое удаление записей по фильтру с коммитом
- **Параметры:** `filters` - фильтры для удаления
- **Возвращает:** `int` - количество удаленных записей
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    deleted_count = await uow.asteroid_repo.bulk_delete(
        filters={"estimated_diameter_km__lt": 0.01}
    )
    print(f"Удалено {deleted_count} маленьких астероидов")
```

## 🔄 **УПРАВЛЕНИЕ ТРАНЗАКЦИЯМИ (transaction)**

### **UnitOfWork**
**Расположение:** `shared/transaction/uow.py`

**Назначение:** Реализация паттерна Unit of Work для управления транзакциями и сессиями базы данных.

**Атрибуты:**
- `session_factory`: Фабрика сессий SQLAlchemy
- `_session`: Текущая сессия
- `_repositories`: Кешированные репозитории
- `asteroid_repo`: Репозиторий астероидов
- `approach_repo`: Репозиторий сближений
- `threat_repo`: Репозиторий угроз

**Методы:**

#### **`__init__(session_factory)`**
- **Назначение:** Инициализирует UnitOfWork

#### **`get_session() -> AsyncSession`**
- **Назначение:** Получить текущую сессию или создать новую
- **Возвращает:** `AsyncSession` - асинхронная сессия SQLAlchemy
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    session = uow.get_session()
    # Работа с сессией напрямую
```

#### **`get_repository(repository_cls: Type[AbstractRepository]) -> AbstractRepository`**
- **Назначение:** Получить или создать экземпляр репозитория, привязанный к текущей сессии
- **Параметры:** `repository_cls` - класс репозитория
- **Возвращает:** `AbstractRepository` - экземпляр репозитория
- **Пример:**
```python
from domains.asteroid.repositories.asteroid_repository import AsteroidRepository

async with UnitOfWork(AsyncSessionLocal) as uow:
    repo = uow.get_repository(AsteroidRepository)
    # Работа с репозиторием
```

#### **`commit()`**
- **Назначение:** Зафиксировать текущую транзакцию
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    # Выполнение операций
    await uow.commit()  # Фиксация изменений
```

#### **`rollback()`**
- **Назначение:** Откатить текущую транзакцию
- **Пример:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    try:
        # Выполнение операций
        pass
    except Exception:
        await uow.rollback()  # Откат изменений
```

#### **`__aenter__()` и `__aexit__()`**
- **Назначение:** Контекстный менеджер для работы с транзакциями
- **Пример:**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async with UnitOfWork(AsyncSessionLocal) as uow:
    # Работа с репозиториями в рамках одной транзакции
    asteroid = await uow.asteroid_repo.get_by_designation("433")
    approaches = await uow.approach_repo.get_by_asteroid(asteroid.id)
    
    # Все изменения будут зафиксированы вместе при выходе из блока
    await uow.commit()
```

## 🧪 **ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ИНФРАСТРУКТУРНЫХ КОМПОНЕНТОВ**

### **Пример использования BaseRepository:**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async with UnitOfWork(AsyncSessionLocal) as uow:
    # Использование универсального фильтра
    filtered_asteroids = await uow.asteroid_repo.filter(
        filters={
            "estimated_diameter_km__ge": 1.0,  # Диаметр >= 1 км
            "earth_moid_au__le": 0.05         # MOID <= 0.05 а.е.
        },
        order_by="estimated_diameter_km",
        order_desc=True
    )
    
    print(f"Найдено {len(filtered_asteroids)} крупных потенциально опасных астероидов")
    
    # Получить статистику
    count = await uow.asteroid_repo.count()
    print(f"Всего астероидов в базе: {count}")
```

### **Пример сложной транзакции:**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async with UnitOfWork(AsyncSessionLocal) as uow:
    try:
        # Создать новый астероид
        new_asteroid = await uow.asteroid_repo.create({
            "designation": "2023_test",
            "name": "Test Asteroid",
            "absolute_magnitude": 20.0,
            "estimated_diameter_km": 0.1,
            "albedo": 0.15
        })
        
        # Создать сближение для этого астероида
        from datetime import datetime
        new_approach = await uow.approach_repo.create({
            "asteroid_id": new_asteroid.id,
            "approach_time": datetime.now(),
            "distance_au": 0.02,
            "distance_km": 0.02 * 149597870.7,
            "velocity_km_s": 15.5,
            "asteroid_designation": new_asteroid.designation,
            "data_source": "Manual Entry"
        })
        
        # Создать оценку угрозы
        new_threat = await uow.threat_repo.create({
            "asteroid_id": new_asteroid.id,
            "designation": new_asteroid.designation,
            "fullname": new_asteroid.name or new_asteroid.designation,
            "ip": 0.001,
            "ts_max": 1,
            "ps_max": -3.0,
            "diameter": new_asteroid.estimated_diameter_km,
            "v_inf": 15.5,
            "h": new_asteroid.absolute_magnitude,
            "n_imp": 1,
            "impact_years": [2025],
            "last_obs": "2023-01-01",
            "threat_level_ru": "ОЧЕНЬ НИЗКИЙ",
            "torino_scale_ru": "1 — Нормальный (зелёный)",
            "impact_probability_text_ru": "0.1% (1 к 1,000)",
            "energy_megatons": 100.0,
            "impact_category": "локальный",
            "sentry_last_update": datetime.now()
        })
        
        # Все изменения будут зафиксированы вместе
        await uow.commit()
        print(f"Созданы астероид {new_asteroid.id}, сближение {new_approach.id}, угроза {new_threat.id}")
        
    except Exception as e:
        await uow.rollback()
        print(f"Ошибка транзакции: {e}")
```

### **Пример использования поиска:**
```python
async with UnitOfWork(AsyncSessionLocal) as uow:
    # Поиск астероидов по имени или обозначению
    search_results = await uow.asteroid_repo.search(
        search_term="eros",
        search_fields=["name", "designation"],
        limit=20
    )
    
    print(f"Найдено {len(search_results)} астероидов по запросу 'eros'")
    
    for asteroid in search_results:
        print(f"- {asteroid.designation}: {asteroid.name}")
```

---

**Следующий раздел:** [ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ](examples.md) - практические примеры работы с каждым компонентом