"""
API роутеры для работы со сближениями астероидов с Землёй.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

from .dependencies import get_approach_service
from domains.approach.services.approach_service import ApproachService

router = APIRouter(prefix="/approaches", tags=["Approaches"])


# === СПЕЦИФИЧНЫЕ МАРШРУТЫ (должны быть ПЕРЕД параметрами пути) ===

@router.get("/upcoming", response_model=List[dict])
async def get_upcoming_approaches(
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество сближений"),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[dict]:
    """
    📅 Получить ближайшие сближения астероидов с Землёй.
    
    Возвращает сближения, отсортированные по времени (ближайшие первыми).
    """
    return await approach_service.get_upcoming(limit=limit)


@router.get("/closest", response_model=List[dict])
async def get_closest_approaches(
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество сближений"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[dict]:
    """
    📏 Получить самые близкие по расстоянию сближения.
    
    Возвращает сближения, отсортированные по расстоянию (самые близкие первыми).
    """
    return await approach_service.get_closest(limit=limit, skip=skip)


@router.get("/fastest", response_model=List[dict])
async def get_fastest_approaches(
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество сближений"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[dict]:
    """
    ⚡ Получить сближения с наибольшей скоростью.
    
    Возвращает сближения, отсортированные по скорости (самые быстрые первыми).
    """
    return await approach_service.get_fastest(limit=limit, skip=skip)


@router.get("/in-period", response_model=List[dict])
async def get_approaches_in_period(
    start_date: datetime = Query(..., description="Начало временного периода"),
    end_date: datetime = Query(..., description="Конец временного периода"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    max_distance: Optional[float] = Query(
        None, 
        ge=0.0, 
        description="Максимальное расстояние в а.е. для фильтрации"
    ),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[dict]:
    """
    📅 Получить сближения в заданном временном промежутке.
    
    Возвращает сближения, произошедшие (или запланированные) в указанный 
    временной период, с возможностью фильтрации по максимальному расстоянию.
    
    - **start_date**: Начало временного периода (ISO 8601)
    - **end_date**: Конец временного периода (ISO 8601)
    - **max_distance**: Опционально, максимальное расстояние в а.е.
    """
    return await approach_service.get_approaches_in_period(
        start_date=start_date,
        end_date=end_date,
        max_distance=max_distance,
        skip=skip,
        limit=limit
    )


@router.get("/statistics")
async def get_approach_statistics(
    approach_service: ApproachService = Depends(get_approach_service)
) -> dict:
    """
    📈 Получить статистику по сближениям.
    
    Возвращает общую статистику: количество сближений, среднее расстояние, 
    среднюю скорость и другую полезную информацию.
    """
    return await approach_service.get_statistics()


# === МАРШРУТЫ С ПАРАМЕТРАМИ ПУТИ (должны быть ПОСЛЕ специфичных) ===

@router.get("/by-id/{asteroid_id}", response_model=List[dict])
async def get_approaches_by_asteroid_id(
    asteroid_id: int,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[dict]:
    """
    🔍 Получить все сближения для астероида по его ID.

    - **asteroid_id**: Уникальный идентификатор астероида
    """
    return await approach_service.get_by_asteroid_id(
        asteroid_id=asteroid_id,
        skip=skip,
        limit=limit
    )


@router.get("/by-designation/{designation}", response_model=List[dict])
async def get_approaches_by_asteroid_designation(
    designation: str,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[dict]:
    """
    🔍 Получить все сближения для астероида по его обозначению NASA.

    - **designation**: Обозначение астероида в системе NASA
    """
    return await approach_service.get_by_asteroid_designation(
        designation=designation,
        skip=skip,
        limit=limit
    )
