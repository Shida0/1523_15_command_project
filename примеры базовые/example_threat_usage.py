"""
Пример использования сервиса угроз без UOW и репозиториев.

Этот пример показывает, как использовать сервисы напрямую с зависимостями FastAPI.
"""

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from shared.database.engine import AsyncSessionLocal
from domains.threat.services.threat_service import ThreatService


# Определяем зависимости для получения сервисов
def get_threat_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)
) -> ThreatService:
    """
    Зависимость для получения сервиса угроз.
    
    Args:
        session_factory: Фабрика сессий SQLAlchemy
        
    Returns:
        ThreatService: Экземпляр сервиса угроз
    """
    return ThreatService(session_factory)


# Пример использования в FastAPI приложении
app = FastAPI()


@app.get("/threats/{designation}")
async def get_threat_by_designation(
    designation: str,
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить оценку угрозы по обозначению астероида.
    
    Args:
        designation: Обозначение астероида в системе NASA
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Данные об оценке угрозы или None, если не найдена
    """
    threat = await threat_service.get_by_designation(designation)
    return {"threat": threat}


@app.get("/threats/asteroid/{asteroid_id}")
async def get_threat_by_asteroid_id(
    asteroid_id: int,
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить оценку угрозы для астероида по его ID.
    
    Args:
        asteroid_id: Уникальный идентификатор астероида
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Данные об оценке угрозы или None, если не найдена
    """
    threat = await threat_service.get_by_asteroid_id(asteroid_id)
    return {"threat": threat}


@app.get("/threats/high-risk")
async def get_high_risk_threats(
    limit: int = 20,
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить угрозы с высоким уровнем риска (туринская шкала >= 5).
    
    Args:
        limit: Максимальное количество возвращаемых угроз
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Список угроз с высоким уровнем риска
    """
    threats = await threat_service.get_high_risk(limit)
    return {"threats": threats, "count": len(threats)}


@app.get("/threats/risk-level")
async def get_threats_by_risk_level(
    min_ts: int = 0,
    max_ts: int = 10,
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить угрозы по диапазону значений Туринской шкалы.
    
    Args:
        min_ts: Минимальное значение по Туринской шкале
        max_ts: Максимальное значение по Туринской шкале
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Список угроз в заданном диапазоне значений Туринской шкалы
    """
    threats = await threat_service.get_by_risk_level(min_ts, max_ts)
    return {"threats": threats, "count": len(threats)}


@app.get("/threats/energy-range")
async def get_threats_by_energy_range(
    min_energy: float = 0.0,
    max_energy: float = None,
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить угрозы по диапазону энергии воздействия.
    
    Args:
        min_energy: Минимальная энергия воздействия в мегатоннах
        max_energy: Максимальная энергия воздействия в мегатоннах
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Список угроз в заданном диапазоне энергии воздействия
    """
    threats = await threat_service.get_by_energy(min_energy, max_energy)
    return {"threats": threats, "count": len(threats)}


@app.get("/threats/category/{category}")
async def get_threats_by_category(
    category: str,
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить угрозы по категории воздействия.
    
    Args:
        category: Категория воздействия (например, "Mercury", "Venus", "Earth", "Mars", "Jupiter")
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Список угроз указанной категории воздействия
    """
    threats = await threat_service.get_by_category(category)
    return {"threats": threats, "count": len(threats)}


@app.get("/threats/statistics")
async def get_threat_statistics(
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить статистику по оценкам угроз астероидов.
    
    Args:
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Статистика по оценкам угроз
    """
    stats = await threat_service.get_statistics()
    return {"statistics": stats}


# Пример использования вне FastAPI (например, в скрипте)
async def standalone_example():
    """
    Пример использования сервиса угроз вне контекста FastAPI.
    """
    # Создаем фабрику сессий
    session_factory = AsyncSessionLocal
    
    # Создаем экземпляр сервиса
    threat_service = ThreatService(session_factory)
    
    # Примеры использования методов сервиса
    print("=== Примеры использования сервиса угроз ===")
    
    # Получить угрозу по обозначению
    threat = await threat_service.get_by_designation("433")
    if threat:
        print(f"Угроза для 433: Туринская шкала = {threat['ts_max']}")
    
    # Получить угрозы высокого риска
    high_risk = await threat_service.get_high_risk(10)
    print(f"Угрозы высокого риска: {len(high_risk)}")
    
    # Получить угрозы по диапазону риска
    medium_risk = await threat_service.get_by_risk_level(2, 4)
    print(f"Угрозы среднего риска (2-4): {len(medium_risk)}")
    
    # Получить статистику
    stats = await threat_service.get_statistics()
    print(f"Всего оценок угроз: {stats['total_threats']}")
    print(f"Угроз высокого риска: {stats['high_risk_count']}")


if __name__ == "__main__":
    import asyncio
    
    # Запуск примера вне FastAPI
    asyncio.run(standalone_example())