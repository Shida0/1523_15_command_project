from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

from .dependencies import get_approach_service
from domains.approach import ApproachResponse, ApproachService

router = APIRouter(prefix="/approaches", tags=["Approaches"])


@router.get("/upcoming")
async def get_upcoming_approaches(
    limit: Optional[int] = Query(),
    skip: int = Query(0),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[ApproachResponse]:
    """Получить ближайшие сближения астероидов с Землёй. Возвращает сближения, отсортированные по времени"""
    return await approach_service.get_upcoming(limit, skip)

@router.get("/closest")
async def get_closest_approaches(
    limit: Optional[int] = Query(),
    skip: int = Query(),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[ApproachResponse]:
    """Получить самые близкие по расстоянию сближения. Возвращает сближения, отсортированные по расстоянию (самые близкие первыми)"""
    return await approach_service.get_closest(limit, skip)

@router.get("/fastest")
async def get_fastest_approaches(
    limit: Optional[int] = Query(),
    skip: int = Query(),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[ApproachResponse]:
    """Получить сближения с наибольшей скоростью. Возвращает сближения, отсортированные по скорости"""
    return await approach_service.get_fastest(limit, skip)

@router.get("/in-period")
async def get_approaches_in_period(
    start_date: datetime = Query(),
    end_date: datetime = Query(),
    skip: int = Query(),
    limit: Optional[int] = Query(),
    max_distance: Optional[float] = Query(),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[ApproachResponse]:
    """Получить сближения в заданном временном промежутке. Возвращает сближения в указанный период с фильтрацией по максимальному расстоянию"""
    return await approach_service.get_approaches_in_period(start_date, end_date, max_distance, skip, limit)

@router.get("/statistics")
async def get_approach_statistics(approach_service: ApproachService = Depends(get_approach_service)) -> dict:
    """Получить статистику по сближениям. Возвращает общую статистику: количество сближений, среднее расстояние, среднюю скорость"""
    return await approach_service.get_statistics()

@router.get("/count")
async def get_approaches_count(approach_service: ApproachService = Depends(get_approach_service)) -> dict:
    """Получить общее количество сближений. Возвращает общее количество сближений в базе данных"""
    count = await approach_service.get_count()
    return {"total": count}

@router.get("/by-id/{asteroid_id}")
async def get_approaches_by_asteroid_id(
    asteroid_id: int,
    skip: int = Query(),
    limit: Optional[int] = Query(),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[ApproachResponse]:
    """Получить все сближения для астероида по его ID"""
    return await approach_service.get_by_asteroid_id(asteroid_id, skip, limit)

@router.get("/by-designation/{designation}")
async def get_approaches_by_asteroid_designation(
    designation: str,
    skip: int = Query(),
    limit: Optional[int] = Query(),
    approach_service: ApproachService = Depends(get_approach_service)
) -> List[ApproachResponse]:
    """Получить все сближения для астероида по его обозначению NASA"""
    return await approach_service.get_by_asteroid_designation(designation, skip, limit)
