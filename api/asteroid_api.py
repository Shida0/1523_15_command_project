"""
API роутеры для работы с астероидами.
"""
from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Optional

from .dependencies import get_asteroid_service, get_approach_service, get_threat_service
from domains.asteroid.schemas import AsteroidResponse, AsteroidDetailResponse
from domains.asteroid.services.asteroid_service import AsteroidService
from domains.approach.services.approach_service import ApproachService
from domains.threat.services.threat_service import ThreatService

router = APIRouter(prefix="/asteroids", tags=["Asteroids"])


@router.get("/near-earth", response_model=List[AsteroidResponse])
async def get_near_earth_asteroids(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    max_moid: float = Query(
        0.05, 
        ge=0.0, 
        le=0.5, 
        description="Максимальное значение MOID (а.е.) для околоземных астероидов"
    ),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[dict]:
    """
    🌍 Получить околоземные астероиды (PHA).
    
    Возвращает астероиды с минимальным расстоянием пересечения орбит (MOID) 
    меньше указанного значения. По умолчанию возвращает потенциально опасные 
    астероиды (PHA) с MOID ≤ 0.05 а.е.
    """
    return await asteroid_service.get_by_moid(max_moid=max_moid, skip=skip, limit=limit)


@router.get("/all", response_model=List[AsteroidResponse])
async def get_all_asteroids(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[dict]:
    """
    📋 Получить все астероиды.
    
    Возвращает список всех астероидов в базе данных с поддержкой пагинации.
    """
    return await asteroid_service.get_by_moid(max_moid=1.0, skip=skip, limit=limit)


@router.get("/orbit-class/{orbit_class}", response_model=List[AsteroidResponse])
async def get_asteroids_by_orbit_class(
    orbit_class: str,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[dict]:
    """
    📊 Получить астероиды по классу орбиты.
    
    Поддерживаемые классы орбит:
    - **Apollo**: орбита пересекает орбиту Земли, большая полуось > 1 а.е.
    - **Aten**: орбита пересекает орбиту Земли, большая полуось < 1 а.е.
    - **Amor**: орбита расположена между орбитами Земли и Марса
    """
    return await asteroid_service.get_by_orbit_class(
        orbit_class, skip=skip, limit=limit
    )


@router.get("/accurate-diameter", response_model=List[AsteroidResponse])
async def get_asteroids_with_accurate_diameter(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> List[dict]:
    """
    📏 Получить астероиды с точными данными о диаметре.
    
    Возвращает астероиды, у которых диаметр измерен напрямую, 
    а не рассчитан по альбедо.
    """
    return await asteroid_service.get_with_accurate_diameter(skip=skip, limit=limit)


@router.get("/statistics")
async def get_asteroid_statistics(
    asteroid_service: AsteroidService = Depends(get_asteroid_service)
) -> dict:
    """
    📈 Получить статистику по астероидам.
    
    Возвращает общую статистику: количество астероидов, средний диаметр, 
    минимальный MOID и другую полезную информацию.
    """
    return await asteroid_service.get_statistics()


@router.get("/{designation}", response_model=AsteroidDetailResponse)
async def get_asteroid_by_designation(
    designation: str,
    asteroid_service: AsteroidService = Depends(get_asteroid_service),
    approach_service: ApproachService = Depends(get_approach_service),
    threat_service: ThreatService = Depends(get_threat_service)
) -> dict:
    """
    🔍 Получить детальную информацию об астероиде.
    
    Возвращает полную информацию об астероиде, включая все его сближения 
    с Землёй и оценку угрозы (если существует).
    
    - **designation**: Обозначение астероида в системе NASA
    """
    # Get asteroid data
    asteroid = await asteroid_service.get_by_designation(designation)
    if not asteroid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asteroid '{designation}' not found"
        )
    
    # Get close approaches for this asteroid
    approaches = await approach_service.get_by_asteroid_designation(designation)
    
    # Get threat assessment for this asteroid
    threat = await threat_service.get_by_designation(designation)
    
    # Build detailed response
    return {
        **asteroid,
        "close_approaches": approaches if approaches else [],
        "threat_assessment": threat
    }
