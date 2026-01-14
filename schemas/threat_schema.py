"""
Pydantic схемы для оценок угроз.
"""
from typing import List
from pydantic import Field
from .base_schema import BaseSchema, CreateSchema

class ThreatAssessmentBase(BaseSchema):
    """Базовая схема оценки угрозы."""
    asteroid_id: int
    designation: str
    fullname: str
    ip: float = Field(ge=0.0, le=1.0)  # Вероятность столкновения
    ts_max: int = Field(ge=0, le=10)  # Туринская шкала
    ps_max: float  # Палермская шкала
    diameter_km: float = Field(ge=0.0)
    velocity_km_s: float = Field(ge=0.0)
    absolute_magnitude: float
    n_imp: int = Field(ge=0)  # Количество сценариев
    impact_years: List[int]
    last_obs: str
    threat_level_ru: str
    torino_scale_ru: str
    impact_probability_text_ru: str
    energy_megatons: float = Field(ge=0.0)
    impact_category: str

class ThreatAssessmentCreate(CreateSchema):
    """Схема для создания оценки угрозы."""
    asteroid_id: int
    designation: str
    fullname: str
    ip: float = Field(ge=0.0, le=1.0)
    ts_max: int = Field(ge=0, le=10)
    ps_max: float
    diameter_km: float = Field(ge=0.0)
    velocity_km_s: float = Field(ge=0.0)
    absolute_magnitude: float
    n_imp: int = Field(ge=0)
    impact_years: List[int]
    last_obs: str
    threat_level_ru: str
    torino_scale_ru: str
    impact_probability_text_ru: str
    energy_megatons: float = Field(default=0.0, ge=0.0)
    impact_category: str = "локальный"

class ThreatAssessmentResponse(ThreatAssessmentBase):
    """Схема для ответа API с оценкой угрозы."""
    pass