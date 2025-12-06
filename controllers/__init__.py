"""
Пакет контроллеров для работы с базой данных.
Содержит контроллеры для астероидов, сближений и оценок угроз.
"""

from .base_controller import BaseController
from .asteroid_controller import AsteroidController
from .approach_controller import ApproachController
from .threat_controller import ThreatController

__all__ = [
    'BaseController',
    'AsteroidController',
    'ApproachController',
    'ThreatController'
]

# Создаем экземпляры контроллеров для удобства использования
asteroid_controller = AsteroidController()
approach_controller = ApproachController()
threat_controller = ThreatController()