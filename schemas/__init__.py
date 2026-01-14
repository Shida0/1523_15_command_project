"""
Инициализация схем.
Импортируем из отдельных файлов для удобства.
"""
from .base_schema import BaseSchema, CreateSchema
from .asteroid_schema import (
    AsteroidBase,
    AsteroidCreate,
    AsteroidResponse
)
from .approach_schema import (
    ApproachBase,
    ApproachCreate,
    ApproachResponse
)
from .threat_schema import (
    ThreatAssessmentBase,
    ThreatAssessmentCreate,
    ThreatAssessmentResponse
)

__all__ = [
    'BaseSchema',
    'CreateSchema',
    'AsteroidBase',
    'AsteroidCreate',
    'AsteroidResponse',
    'ApproachBase',
    'ApproachCreate',
    'ApproachResponse',
    'ThreatAssessmentBase',
    'ThreatAssessmentCreate',
    'ThreatAssessmentResponse'
]