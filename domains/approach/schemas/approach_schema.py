"""
Pydantic схемы для сближений.
"""
from datetime import datetime
from typing import Optional
from shared.infrastructure import BaseSchema, CreateSchema

class ApproachBase(BaseSchema):
    """Базовая схема сближения."""
    asteroid_id: int
    approach_time: datetime
    distance_au: float
    distance_km: float
    velocity_km_s: float
    asteroid_designation: str
    asteroid_name: Optional[str] = None
    data_source: str
    calculation_batch_id: Optional[str] = None

class ApproachCreate(CreateSchema):
    """Схема для создания сближения."""
    asteroid_id: int
    approach_time: datetime
    distance_au: float
    velocity_km_s: float
    asteroid_designation: str
    asteroid_name: Optional[str] = None
    data_source: str = "NASA CAD API"
    calculation_batch_id: Optional[str] = None

class ApproachResponse(ApproachBase):
    """Схема для ответа API со сближением."""
    pass