"""
API роутеры для работы с оценками угроз астероидов.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from .dependencies import get_threat_service
from domains.threat.services.threat_service import ThreatService

router = APIRouter(prefix="/threats", tags=["Threats"])


@router.get("/current", response_model=List[dict])
async def get_current_threats(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=500, description="Максимальное количество записей"),
    min_ts: int = Query(
        0, 
        ge=0, 
        le=10, 
        description="Минимальная шкала Турина для фильтрации"
    ),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[dict]:
    """
    ⚠️ Получить актуальные угрозы.
    
    Возвращает список объектов с ненулевым риском, отсортированных по степени опасности.
    """
    return await threat_service.get_by_risk_level(
        min_ts=min_ts, max_ts=10, skip=skip, limit=limit
    )


@router.get("/high-risk", response_model=List[dict])
async def get_high_risk_threats(
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество угроз"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[dict]:
    """
    🚨 Получить угрозы высокого риска.

    Возвращает угрозы с Туринской шкалой >= 5 (значительная вероятность
    столкновения с серьезными последствиями).
    """
    return await threat_service.get_high_risk(limit=limit, skip=skip)


@router.get("/by-probability", response_model=List[dict])
async def get_threats_by_probability(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=500, description="Максимальное количество записей"),
    min_probability: float = Query(
        0.0, 
        ge=0.0, 
        le=1.0, 
        description="Минимальная вероятность столкновения"
    ),
    max_probability: float = Query(
        1.0, 
        ge=0.0, 
        le=1.0, 
        description="Максимальная вероятность столкновения"
    ),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[dict]:
    """
    🎯 Получить угрозы по диапазону вероятности столкновения.
    """
    return await threat_service.get_by_probability(
        min_probability=min_probability,
        max_probability=max_probability,
        skip=skip,
        limit=limit
    )


@router.get("/by-energy", response_model=List[dict])
async def get_threats_by_energy(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=500, description="Максимальное количество записей"),
    min_energy: float = Query(
        0.0, 
        ge=0.0, 
        description="Минимальная энергия воздействия (Мт)"
    ),
    max_energy: Optional[float] = Query(
        None, 
        ge=0.0, 
        description="Максимальная энергия воздействия (Мт)"
    ),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[dict]:
    """
    💥 Получить угрозы по диапазону энергии воздействия.
    
    Энергия измеряется в мегатоннах (Мт).
    """
    return await threat_service.get_by_energy(
        min_energy=min_energy,
        max_energy=max_energy,
        skip=skip,
        limit=limit
    )


@router.get("/statistics")
async def get_threat_statistics(
    threat_service: ThreatService = Depends(get_threat_service)
) -> dict:
    """
    📈 Получить статистику по угрозам.
    
    Возвращает общую статистику: количество угроз, распределение по 
    уровням риска и другую полезную информацию.
    """
    return await threat_service.get_statistics()


@router.get("/{designation}")
async def get_threat_by_designation(
    designation: str,
    threat_service: ThreatService = Depends(get_threat_service)
) -> Optional[dict]:
    """
    🔍 Получить угрозу для конкретного астероида.

    - **designation**: Обозначение астероида в системе NASA

    Возвращает оценку угрозы или None, если угроза не найдена.
    """
    return await threat_service.get_by_designation(designation)


@router.get("/by-category/{category}", response_model=List[dict])
async def get_threats_by_category(
    category: str,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=500, description="Максимальное количество записей"),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[dict]:
    """
    📋 Получить угрозы по категории воздействия.
    
    Категории: Mercury, Venus, Earth, Mars, Jupiter
    """
    return await threat_service.get_by_category(
        category=category,
        skip=skip,
        limit=limit
    )
