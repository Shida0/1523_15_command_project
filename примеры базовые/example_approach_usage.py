"""
Пример использования сервиса сближений без UOW и репозиториев.

Этот пример показывает, как использовать сервисы напрямую с зависимостями FastAPI.
"""

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from shared.database.engine import AsyncSessionLocal
from domains.approach.services.approach_service import ApproachService


# Определяем зависимости для получения сервисов
def get_approach_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)
) -> ApproachService:
    """
    Зависимость для получения сервиса сближений.
    
    Args:
        session_factory: Фабрика сессий SQLAlchemy
        
    Returns:
        ApproachService: Экземпляр сервиса сближений
    """
    return ApproachService(session_factory)


# Пример использования в FastAPI приложении
app = FastAPI()


@app.get("/approaches/upcoming")
async def get_upcoming_approaches(
    limit: int = 10,
    approach_service: ApproachService = Depends(get_approach_service)
):
    """
    Получить ближайшие сближения астероидов с Землей.
    
    Args:
        limit: Максимальное количество возвращаемых сближений
        approach_service: Сервис для работы со сближениями
        
    Returns:
        Список ближайших сближений
    """
    approaches = await approach_service.get_upcoming(limit)
    return {"approaches": approaches, "count": len(approaches)}


@app.get("/approaches/closest")
async def get_closest_approaches(
    limit: int = 10,
    approach_service: ApproachService = Depends(get_approach_service)
):
    """
    Получить самые близкие по расстоянию сближения.
    
    Args:
        limit: Максимальное количество возвращаемых сближений
        approach_service: Сервис для работы со сближениями
        
    Returns:
        Список сближений, отсортированных по расстоянию
    """
    approaches = await approach_service.get_closest(limit)
    return {"approaches": approaches, "count": len(approaches)}


@app.get("/approaches/fastest")
async def get_fastest_approaches(
    limit: int = 10,
    approach_service: ApproachService = Depends(get_approach_service)
):
    """
    Получить сближения с наибольшей скоростью.
    
    Args:
        limit: Максимальное количество возвращаемых сближений
        approach_service: Сервис для работы со сближениями
        
    Returns:
        Список сближений, отсортированных по скорости
    """
    approaches = await approach_service.get_fastest(limit)
    return {"approaches": approaches, "count": len(approaches)}


@app.get("/approaches/asteroid/{asteroid_id}")
async def get_approaches_by_asteroid_id(
    asteroid_id: int,
    approach_service: ApproachService = Depends(get_approach_service)
):
    """
    Получить все сближения для астероида по его ID.
    
    Args:
        asteroid_id: Уникальный идентификатор астероида
        approach_service: Сервис для работы со сближениями
        
    Returns:
        Список всех сближений для указанного астероида
    """
    approaches = await approach_service.get_by_asteroid_id(asteroid_id)
    return {"approaches": approaches, "count": len(approaches)}


@app.get("/approaches/asteroid-designation/{designation}")
async def get_approaches_by_asteroid_designation(
    designation: str,
    approach_service: ApproachService = Depends(get_approach_service)
):
    """
    Получить все сближения для астероида по его обозначению NASA.
    
    Args:
        designation: Обозначение астероида в системе NASA
        approach_service: Сервис для работы со сближениями
        
    Returns:
        Список всех сближений для астероида с указанным обозначением
    """
    approaches = await approach_service.get_by_asteroid_designation(designation)
    return {"approaches": approaches, "count": len(approaches)}


@app.get("/approaches/statistics")
async def get_approach_statistics(
    approach_service: ApproachService = Depends(get_approach_service)
):
    """
    Получить статистику по сближениям астероидов с Землей.
    
    Args:
        approach_service: Сервис для работы со сближениями
        
    Returns:
        Статистика по сближениям
    """
    stats = await approach_service.get_statistics()
    return {"statistics": stats}


# Пример использования вне FastAPI (например, в скрипте)
async def standalone_example():
    """
    Пример использования сервиса сближений вне контекста FastAPI.
    """
    # Создаем фабрику сессий
    session_factory = AsyncSessionLocal
    
    # Создаем экземпляр сервиса
    approach_service = ApproachService(session_factory)
    
    # Примеры использования методов сервиса
    print("=== Примеры использования сервиса сближений ===")
    
    # Получить ближайшие сближения
    upcoming = await approach_service.get_upcoming(5)
    print(f"Ближайшие 5 сближений: {len(upcoming)}")
    
    # Получить самые близкие сближения
    closest = await approach_service.get_closest(5)
    print(f"Самые близкие 5 сближений: {len(closest)}")
    
    # Получить самые быстрые сближения
    fastest = await approach_service.get_fastest(5)
    print(f"Самые быстрые 5 сближений: {len(fastest)}")
    
    # Получить статистику
    stats = await approach_service.get_statistics()
    print(f"Всего сближений: {stats['total_approaches']}")
    print(f"Среднее расстояние: {stats['avg_distance_au']} а.е.")


if __name__ == "__main__":
    import asyncio
    
    # Запуск примера вне FastAPI
    asyncio.run(standalone_example())