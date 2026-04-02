"""
API роутеры для работы с астероидами.
"""
from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Optional, Dict, Any

from .dependencies import get_asteroid_service, get_approach_service, get_threat_service
from domains.asteroid import AsteroidResponse, AsteroidDetailResponse, AsteroidService
from domains.approach import ApproachResponse, ApproachService
from domains.threat import ThreatAssessmentResponse, ThreatService

router = APIRouter(prefix="/asteroids", tags=["Asteroids"])


@router.get("/near-earth")
async def get_near_earth_asteroids(
    skip: int = Query(0),
    limit: Optional[int] = Query(),
    max_moid: float = Query(default=0.05, description="Максимальный MOID в AU"),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[AsteroidResponse]:
    """Получить околоземные астероиды (PHA). Возвращает астероиды с MOID меньше указанного значения"""
    return await asteroid_service.get_by_moid(max_moid, skip, limit)

@router.get("/all")
async def get_all_asteroids(
    skip: int = Query(),
    limit: Optional[int] = Query(),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[AsteroidResponse]:
    """Получить все астероиды. Возвращает список всех астероидов в базе данных с поддержкой пагинации"""
    return await asteroid_service.get_all(skip, limit)

@router.get("/count")
async def get_asteroids_count(asteroid_service: AsteroidService = Depends(get_asteroid_service)) -> dict:
    """Получить общее количество астероидов. Возвращает общее количество астероидов в базе данных"""
    count = await asteroid_service.get_count(max_moid=1.0)
    return {"total": count}

@router.get("/orbit-class/{orbit_class}")
async def get_asteroids_by_orbit_class(
    orbit_class: str,
    skip: int = Query(0),
    limit: Optional[int] = Query(),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[AsteroidResponse]:
    """Получить астероиды по классу орбиты. Поддерживаемые классы: Apollo, Aten, Amor"""
    if orbit_class not in ["Apollo", "Aten", "Amor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid orbit class: {orbit_class}. Supported: Apollo, Aten, Amor"
        )
    return await asteroid_service.get_by_orbit_class(orbit_class, skip, limit)

@router.get("/accurate-diameter")
async def get_asteroids_with_accurate_diameter(
    skip: int = Query(),
    limit: Optional[int] = Query(),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[AsteroidResponse]:
    """Получить астероиды с точными данными о диаметре. Возвращает астероиды с измеренным диаметром"""
    return await asteroid_service.get_with_accurate_diameter(skip, limit)

@router.get("/statistics")
async def get_asteroid_statistics(asteroid_service: AsteroidService = Depends(get_asteroid_service)) -> dict:
    """Получить статистику по астероидам. Возвращает общую статистику: количество, средний диаметр, минимальный MOID"""
    return await asteroid_service.get_statistics()

@router.get("/{designation}", response_model=AsteroidDetailResponse)
async def get_asteroid_by_designation(
    designation: str,
    asteroid_service: AsteroidService = Depends(get_asteroid_service),
    approach_service: ApproachService = Depends(get_approach_service),
    threat_service: ThreatService = Depends(get_threat_service)
) -> Dict[str, Any]:
    """Получить детальную информацию об астероиде. Возвращает полную информацию включая сближения и оценку угрозы"""
    asteroid = await asteroid_service.get_by_designation(designation)
    if not asteroid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asteroid '{designation}' not found"
        )

    approaches = await approach_service.get_by_asteroid_designation(designation)
    threat = await threat_service.get_by_designation(designation)

    return {
        **asteroid,
        "close_approaches": approaches if approaches else [],
        "threat_assessment": threat
    }
