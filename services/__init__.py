"""
Инициализация сервисов.
"""
from .base_service import BaseService
from .asteroid_service import AsteroidService
from .approach_service import ApproachService
from .threat_service import ThreatService
from .update_service import UpdateService

__all__ = [
    'BaseService',
    'AsteroidService',
    'ApproachService',
    'ThreatService',
    'UpdateService'
]