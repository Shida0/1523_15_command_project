"""
API роутеры для работы со сближениями астероидов с Землёй.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

from .dependencies import get_approach_service
from domains.approach.schemas import ApproachResponse
from domains.approach.services.approach_service import ApproachService

router = APIRouter(prefix="/approaches", tags=["Approaches"])


@router.get("/upcoming", response_model=List[ApproachResponse])
async def get_upcoming_approaches(
    limit: Optional[int] = Query(None, ge=0),
    approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить ближайшие сближения астероидов с Землёй.

    Возвращает сближения, отсортированные по времени.
    """
    return await approach_service.get_upcoming(limit=limit)


@router.get("/closest", response_model=List[ApproachResponse])
async def get_closest_approaches(
    limit: Optional[int] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить самые близкие по расстоянию сближения.

    Возвращает сближения, отсортированные по расстоянию (самые близкие первыми).
    """
    return await approach_service.get_closest(limit=limit, skip=skip)


@router.get("/fastest", response_model=List[ApproachResponse])
async def get_fastest_approaches(
    limit: Optional[int] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить сближения с наибольшей скоростью.

    Возвращает сближения, отсортированные по скорости.
    """
    return await approach_service.get_fastest(limit=limit, skip=skip)


@router.get("/in-period", response_model=List[ApproachResponse])
async def get_approaches_in_period(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=0),
    max_distance: Optional[float] = Query(None, ge=0.0),
    approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить сближения в заданном временном промежутке.

    Возвращает сближения, произошедшие (или запланированные) в указанный
    временной период, с возможностью фильтрации по максимальному расстоянию.

    start_date: Начало временного периода (ISO 8601)
    end_date: Конец временного периода (ISO 8601)
    max_distance: Опционально, максимальное расстояние в а.е.
    """
    return await approach_service.get_approaches_in_period(
        start_date=start_date,
        end_date=end_date,
        max_distance=max_distance,
        skip=skip,
        limit=limit
    )


@router.get("/statistics", response_model=dict)
async def get_approach_statistics(approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить статистику по сближениям.

    Возвращает общую статистику: количество сближений, среднее расстояние,
    среднюю скорость и другую полезную информацию.
    """
    return await approach_service.get_statistics()


@router.get("/count", response_model=dict)
async def get_approaches_count(approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить общее количество сближений.

    Возвращает общее количество сближений в базе данных.
    """
    stats = await approach_service.get_statistics()
    return {"total": stats["total_approaches"]}


@router.get("/by-id/{asteroid_id}", response_model=List[ApproachResponse])
async def get_approaches_by_asteroid_id(
    asteroid_id: int,
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=0),
    approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить все сближения для астероида по его ID.

    asteroid_id: Уникальный идентификатор астероида
    """
    return await approach_service.get_by_asteroid_id(asteroid_id=asteroid_id, skip=skip, limit=limit)


@router.get("/by-designation/{designation}", response_model=List[ApproachResponse])
async def get_approaches_by_asteroid_designation(
    designation: str,
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=0),
    approach_service: ApproachService = Depends(get_approach_service)):
    """
    Получить все сближения для астероида по его обозначению NASA.

    designation: Обозначение астероида в системе NASA
    """
    return await approach_service.get_by_asteroid_designation(designation=designation, skip=skip, limit=limit)
