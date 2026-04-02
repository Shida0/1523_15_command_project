from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import Field
from shared.infrastructure import BaseSchema

class AsteroidBase(BaseSchema):
    """Базовая схема астероида"""
    designation: str
    name: Optional[str] = None
    perihelion_au: Optional[float] = None
    aphelion_au: Optional[float] = None
    earth_moid_au: Optional[float] = None
    absolute_magnitude: float
    estimated_diameter_km: float
    accurate_diameter: bool
    albedo: float = Field(ge=0.0, le=1.0)
    diameter_source: str
    orbit_id: Optional[str] = None
    orbit_class: Optional[str] = None

class AsteroidResponse(AsteroidBase):
    """Схема для ответа API с астероидом"""
    pass


class AsteroidDetailResponse(AsteroidResponse):
    """Расширенная схема ответа с полной информацией об астероиде. Включает все данные астероида, плюс список сближений и оценку угрозы"""
    close_approaches: List[Dict[str, Any]] = []
    threat_assessment: Optional[Dict[str, Any]] = None