"""
API роутеры для работы с оценками угроз астероидов.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from .dependencies import get_threat_service
from domains.threat import ThreatAssessmentResponse, ThreatService

router = APIRouter(prefix="/threats", tags=["Threats"])


@router.get("/current")
async def get_current_threats(
    skip: int = Query(0),
    limit: Optional[int] = Query(),
    min_ts: int = Query(default=1, description="Минимальная Туринская шкала"),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[ThreatAssessmentResponse]:
    """Получить актуальные угрозы. Возвращает список объектов с ненулевым риском, отсортированных по степени опасности"""
    return await threat_service.get_by_risk_level(min_ts, 10, skip, limit)

@router.get("/high-risk")
async def get_high_risk_threats(
    limit: Optional[int] = Query(),
    skip: int = Query(),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[ThreatAssessmentResponse]:
    """Получить угрозы высокого риска. Возвращает угрозы с Туринской шкалой >= 5"""
    return await threat_service.get_high_risk(limit, skip)

@router.get("/by-probability")
async def get_threats_by_probability(
    skip: int = Query(),
    limit: Optional[int] = Query(),
    min_probability: float = Query(),
    max_probability: float = Query(),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[ThreatAssessmentResponse]:
    """Получить угрозы по диапазону вероятности столкновения"""
    return await threat_service.get_by_probability(min_probability, max_probability, skip, limit)

@router.get("/by-energy")
async def get_threats_by_energy(
    skip: int = Query(),
    limit: Optional[int] = Query(),
    min_energy: float = Query(),
    max_energy: Optional[float] = Query(),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[ThreatAssessmentResponse]:
    """Получить угрозы по диапазону энергии воздействия. Энергия измеряется в мегатоннах (Мт)"""
    return await threat_service.get_by_energy(min_energy, max_energy, skip, limit)

@router.get("/statistics")
async def get_threat_statistics(threat_service: ThreatService = Depends(get_threat_service)) -> dict:
    """Получить статистику по угрозам. Возвращает общую статистику: количество угроз, распределение по уровням риска"""
    return await threat_service.get_statistics()

@router.get("/{designation}")
async def get_threat_by_designation(
    designation: str,
    threat_service: ThreatService = Depends(get_threat_service)
) -> ThreatAssessmentResponse:
    """Получить угрозу для конкретного астероида. Возвращает оценку угрозы или None, если угроза не найдена"""
    return await threat_service.get_by_designation(designation)

@router.get("/by-category/{category}")
async def get_threats_by_category(
    category: str,
    skip: int = Query(0),
    limit: Optional[int] = Query(),
    threat_service: ThreatService = Depends(get_threat_service)
) -> List[ThreatAssessmentResponse]:
    """Получить угрозы по категории воздействия. Категории: локальный, региональный, глобальный"""
    if category not in ["локальный", "региональный", "глобальный"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {category}. Supported: локальный, региональный, глобальный"
        )
    return await threat_service.get_by_category(category, skip, limit)
