"""
Пакет сервисов с бизнес-логикой.
Содержит все сервисы для работы с астероидами, сближениями и оценками угроз.
"""

from .base_service import BaseService, ServiceWithController
from .asteroid_service import AsteroidService
from .approach_service import ApproachService
from .threat_service import ThreatAssessmentService
from .update_service import DataUpdateService

__all__ = [
    'BaseService',
    'ServiceWithControler',
    'AsteroidService',
    'ApproachService', 
    'ThreatAssessmentService',
    'DataUpdateService',
    'SpaceMathService'
]

# Создаем экземпляры сервисов для удобства использования
asteroid_service = AsteroidService()
approach_service = ApproachService()
threat_service = ThreatAssessmentService()
update_service = DataUpdateService()
