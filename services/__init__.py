"""
Пакет сервисов - бизнес-логика приложения.
"""
from .asteroid_service import AsteroidService
from .approach_service import ApproachService
from .threat_service import ThreatAssessmentService
from .update_service import DataUpdateService
from .math_service import SpaceMathService

__all__ = [
    'AsteroidService',
    'ApproachService',
    'ThreatAssessmentService',
    'DataUpdateService',
    'SpaceMathService'
]

# Создаем экземпляры сервисов для удобного импорта
asteroid_service = AsteroidService()
approach_service = ApproachService()
threat_service = ThreatAssessmentService()
update_service = DataUpdateService()
math_service = SpaceMathService()