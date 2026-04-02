from typing import List
from pydantic import Field
from shared.infrastructure import BaseSchema

class ThreatAssessmentBase(BaseSchema):
    """Базовая схема оценки угрозы"""
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
    energy_megatons: float = Field(ge=0.0)
    impact_category: str

class ThreatAssessmentResponse(ThreatAssessmentBase):
    """Схема для ответа API с оценкой угрозы"""
    pass
