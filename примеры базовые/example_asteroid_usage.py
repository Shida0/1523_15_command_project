"""
Пример использования сервиса астероидов.

Этот пример показывает, как использовать сервисы напрямую с зависимостями FastAPI.
"""

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from shared.database.engine import AsyncSessionLocal
from domains.asteroid.services.asteroid_service import AsteroidService


# Определяем зависимости для получения сервисов
def get_asteroid_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)
) -> AsteroidService:
    """
    Зависимость для получения сервиса астероидов.
    
    Args:
        session_factory: Фабрика сессий SQLAlchemy
        
    Returns:
        AsteroidService: Экземпляр сервиса астероидов
    """
    return AsteroidService(session_factory)


# Пример использования в FastAPI приложении
app = FastAPI()


@app.get("/asteroids/{designation}")
async def get_asteroid_by_designation(
    designation: str, 
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
):
    """
    Получить информацию об астероиде по его обозначению.
    
    Args:
        designation: Обозначение астероида (например, "433")
        asteroid_service: Сервис для работы с астероидами
        
    Returns:
        Информация об астероиде или None, если не найден
    """
    asteroid = await asteroid_service.get_by_designation(designation)
    return {"asteroid": asteroid}


@app.get("/asteroids/near-earth")
async def get_near_earth_asteroids(
    max_moid: float = 0.05,
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
):
    """
    Получить астероиды с MOID (минимальное расстояние пересечения орбит) меньше указанного.
    
    Args:
        max_moid: Максимальное значение MOID (по умолчанию 0.05 а.е.)
        asteroid_service: Сервис для работы с астероидами
        
    Returns:
        Список астероидов с MOID меньше указанного значения
    """
    asteroids = await asteroid_service.get_by_moid(max_moid)
    return {"asteroids": asteroids, "count": len(asteroids)}


@app.get("/asteroids/orbit-class/{orbit_class}")
async def get_asteroids_by_orbit_class(
    orbit_class: str,
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
):
    """
    Получить астероиды по классу орбиты.
    
    Args:
        orbit_class: Класс орбиты (например, "Apollo", "Aten", "Amor")
        asteroid_service: Сервис для работы с астероидами
        
    Returns:
        Список астероидов указанного класса орбиты
    """
    asteroids = await asteroid_service.get_by_orbit_class(orbit_class)
    return {"asteroids": asteroids, "count": len(asteroids)}


@app.get("/asteroids/statistics")
async def get_asteroid_statistics(
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
):
    """
    Получить статистику по астероидам.
    
    Args:
        asteroid_service: Сервис для работы с астероидами
        
    Returns:
        Статистика по астероидам
    """
    stats = await asteroid_service.get_statistics()
    return {"statistics": stats}


# Пример использования вне FastAPI (например, в скрипте)
async def standalone_example():
    """
    Пример использования сервиса астероидов вне контекста FastAPI.
    """
    # Создаем фабрику сессий
    session_factory = AsyncSessionLocal
    
    # Создаем экземпляр сервиса
    asteroid_service = AsteroidService(session_factory)
    
    # Примеры использования методов сервиса
    print("=== Примеры использования сервиса астероидов ===")
    
    # Получить астероид по обозначению
    asteroid = await asteroid_service.get_by_designation("433")
    if asteroid:
        print(f"Астероид 433: {asteroid['name']}")
    
    # Получить ближайшие к Земле астероиды
    nearby_asteroids = await asteroid_service.get_by_moid(0.05)
    print(f"Найдено {len(nearby_asteroids)} ближайших к Земле астероидов")
    
    # Получить астероиды класса Apollo
    apollo_asteroids = await asteroid_service.get_by_orbit_class("Apollo")
    print(f"Найдено {len(apollo_asteroids)} астероидов класса Apollo")
    
    # Получить статистику
    stats = await asteroid_service.get_statistics()
    print(f"Всего астероидов: {stats['total_asteroids']}")
    print(f"Средний диаметр: {stats['average_diameter_km']} км")


if __name__ == "__main__":
    import asyncio
    
    # Запуск примера вне FastAPI
    asyncio.run(standalone_example())