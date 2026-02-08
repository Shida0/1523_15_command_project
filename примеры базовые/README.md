# Примеры использования бизнес-логики

В этой директории находятся простые примеры использования бизнес-логики вашего приложения без использования UOW (Unit of Work) и репозиториев. Все примеры используют только сервисы с зависимостями FastAPI.

## Содержание

- `example_asteroid_usage.py` - Примеры использования сервиса астероидов
- `example_approach_usage.py` - Примеры использования сервиса сближений
- `example_threat_usage.py` - Примеры использования сервиса угроз
- `example_combined_usage.py` - Комбинированные примеры использования всех сервисов

## Особенности реализации

Все примеры демонстрируют:

1. **Использование сервисов напрямую** - без промежуточных слоев UOW и репозиториев
2. **Зависимости FastAPI** - правильное определение зависимостей для получения сервисов
3. **Работу как внутри, так и вне контекста FastAPI** - примеры показывают использование в FastAPI приложениях и в автономных скриптах
4. **Асинхронную работу с базой данных** - через фабрику сессий SQLAlchemy

## Как использовать

### В FastAPI приложении:

```python
from fastapi import Depends
from domains.asteroid.services.asteroid_service import AsteroidService

def get_asteroid_service(session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)):
    return AsteroidService(session_factory)

@app.get("/asteroids/{designation}")
async def get_asteroid(designation: str, service: AsteroidService = Depends(get_asteroid_service)):
    return await service.get_by_designation(designation)
```

### В автономном скрипте:

```python
from shared.database.engine import AsyncSessionLocal
from domains.asteroid.services.asteroid_service import AsteroidService

session_factory = AsyncSessionLocal
service = AsteroidService(session_factory)

# Использование методов сервиса
result = await service.get_by_designation("433")
```

## Домены

Примеры охватывают три основных домена:

1. **Asteroids** - работа с астероидами (поиск по обозначению, классификация по орбите, статистика)
2. **Approaches** - работа со сближениями астероидов с Землей (ближайшие, самые быстрые, статистика)
3. **Threats** - работа с оценками угроз (по уровню риска, энергии, категории воздействия)

Каждый пример включает как REST API endpoints для использования в FastAPI, так и автономные функции для использования в скриптах.