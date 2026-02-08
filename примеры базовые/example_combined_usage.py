"""
Комбинированный пример использования всех сервисов без UOW и репозиториев.

Этот пример показывает, как использовать все три сервиса (астероиды, сближения, угрозы) 
напрямую с зависимостями FastAPI в одном приложении.
"""

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from shared.database.engine import AsyncSessionLocal
from domains.asteroid.services.asteroid_service import AsteroidService
from domains.approach.services.approach_service import ApproachService
from domains.threat.services.threat_service import ThreatService


# Определяем зависимости для получения всех сервисов
def get_asteroid_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)
) -> AsteroidService:
    """Зависимость для получения сервиса астероидов."""
    return AsteroidService(session_factory)


def get_approach_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)
) -> ApproachService:
    """Зависимость для получения сервиса сближений."""
    return ApproachService(session_factory)


def get_threat_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(lambda: AsyncSessionLocal)
) -> ThreatService:
    """Зависимость для получения сервиса угроз."""
    return ThreatService(session_factory)


# Пример использования в FastAPI приложении
app = FastAPI()


@app.get("/dashboard")
async def get_comprehensive_dashboard(
    asteroid_service: AsteroidService = Depends(get_asteroid_service),
    approach_service: ApproachService = Depends(get_approach_service),
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Комплексная панель управления с информацией по всем доменам.
    
    Args:
        asteroid_service: Сервис для работы с астероидами
        approach_service: Сервис для работы со сближениями
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Комплексная информация по всем доменам
    """
    # Получаем статистику по всем доменам
    asteroid_stats = await asteroid_service.get_statistics()
    approach_stats = await approach_service.get_statistics()
    threat_stats = await threat_service.get_statistics()
    
    # Получаем ближайшие сближения
    upcoming_approaches = await approach_service.get_upcoming(5)
    
    # Получаем угрозы высокого риска
    high_risk_threats = await threat_service.get_high_risk(5)
    
    return {
        "asteroid_statistics": asteroid_stats,
        "approach_statistics": approach_stats,
        "threat_statistics": threat_stats,
        "upcoming_approaches": upcoming_approaches,
        "high_risk_threats": high_risk_threats
    }


@app.get("/asteroid-details/{designation}")
async def get_asteroid_comprehensive_info(
    designation: str,
    asteroid_service: AsteroidService = Depends(get_asteroid_service),
    approach_service: ApproachService = Depends(get_approach_service),
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить комплексную информацию об астероиде по его обозначению.
    
    Args:
        designation: Обозначение астероида в системе NASA
        asteroid_service: Сервис для работы с астероидами
        approach_service: Сервис для работы со сближениями
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Комплексная информация об астероиде
    """
    # Получаем информацию об астероиде
    asteroid = await asteroid_service.get_by_designation(designation)
    
    if not asteroid:
        return {"error": f"Asteroid with designation {designation} not found"}
    
    # Получаем сближения для этого астероида
    approaches = await approach_service.get_by_asteroid_designation(designation)
    
    # Получаем угрозу для этого астероида
    threat = await threat_service.get_by_designation(designation)
    
    return {
        "asteroid": asteroid,
        "approaches": approaches,
        "threat": threat
    }


@app.get("/risk-assessment")
async def get_risk_assessment_summary(
    asteroid_service: AsteroidService = Depends(get_asteroid_service),
    approach_service: ApproachService = Depends(get_approach_service),
    threat_service: ThreatService = Depends(get_threat_service)
):
    """
    Получить сводку по оценке рисков.
    
    Args:
        asteroid_service: Сервис для работы с астероидами
        approach_service: Сервис для работы со сближениями
        threat_service: Сервис для работы с угрозами
        
    Returns:
        Сводка по оценке рисков
    """
    # Получаем астероиды с MOID < 0.05 (потенциально опасные)
    pha_asteroids = await asteroid_service.get_by_moid(0.05)
    
    # Получаем угрозы высокого риска
    high_risk_threats = await threat_service.get_high_risk()
    
    # Получаем ближайшие сближения
    upcoming_approaches = await approach_service.get_upcoming(10)
    
    return {
        "potentially_hazardous_asteroids": {
            "count": len(pha_asteroids),
            "asteroids": pha_asteroids[:5]  # Только первые 5 для примера
        },
        "high_risk_threats": {
            "count": len(high_risk_threats),
            "threats": high_risk_threats
        },
        "upcoming_approaches": {
            "count": len(upcoming_approaches),
            "approaches": upcoming_approaches
        }
    }


# Пример использования вне FastAPI (например, в скрипте)
async def standalone_combined_example():
    """
    Пример использования всех сервисов вместе вне контекста FastAPI.
    """
    # Создаем фабрику сессий
    session_factory = AsyncSessionLocal
    
    # Создаем экземпляры всех сервисов
    asteroid_service = AsteroidService(session_factory)
    approach_service = ApproachService(session_factory)
    threat_service = ThreatService(session_factory)
    
    print("=== Комбинированный пример использования всех сервисов ===")
    
    # Получить статистику по всем доменам
    asteroid_stats = await asteroid_service.get_statistics()
    approach_stats = await approach_service.get_statistics()
    threat_stats = await threat_service.get_statistics()
    
    print(f"Всего астероидов: {asteroid_stats['total_asteroids']}")
    print(f"Всего сближений: {approach_stats['total_approaches']}")
    print(f"Всего оценок угроз: {threat_stats['total_threats']}")
    
    # Получить информацию об определенном астероиде
    asteroid = await asteroid_service.get_by_designation("433")
    if asteroid:
        print(f"\nИнформация об астероиде 433 ({asteroid['name']}):")
        
        # Получить сближения для этого астероида
        approaches = await approach_service.get_by_asteroid_designation("433")
        print(f"  Количество сближений: {len(approaches)}")
        
        # Получить угрозу для этого астероида
        threat = await threat_service.get_by_designation("433")
        if threat:
            print(f"  Уровень угрозы (Туринская шкала): {threat['ts_max']}")
        else:
            print("  Угроза не зарегистрирована")
    
    # Получить риски
    high_risk_threats = await threat_service.get_high_risk(5)
    print(f"\nВысокие риски: {len(high_risk_threats)}")
    
    upcoming_approaches = await approach_service.get_upcoming(5)
    print(f"Ближайшие сближения: {len(upcoming_approaches)}")


if __name__ == "__main__":
    import asyncio
    
    # Запуск примера вне FastAPI
    asyncio.run(standalone_combined_example())