from .base import Base
from .asteroid import AsteroidModel
from .close_approach import CloseApproachModel
from .threat_assessment import ThreatAssessmentModel
from .engine import get_async_session

# Экспортируем все модели для удобства
__all__ = [
    'Base',
    'AsteroidModel',
    'CloseApproachModel', 
    'ThreatAssessmentModel'
]

# Для Alembic autogenerate
metadata = Base.metadata