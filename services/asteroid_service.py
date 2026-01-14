"""
Сервис для работы с астероидами.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from controllers.asteroid_controller import AsteroidController
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AsteroidService(BaseService):
    """
    Сервис для работы с астероидами.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса для астероидов.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        controller = AsteroidController()
        super().__init__(session, controller)
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===
    
    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """
        Получение астероида по обозначению NASA.
        """
        asteroid = await self.controller.get_by_designation(self.session, designation)
        return self._model_to_dict(asteroid) if asteroid else None
    
    async def get_by_moid(self, max_moid: float = 0.05) -> List[Dict[str, Any]]:
        """
        Получение астероидов с MOID меньше указанного.
        """
        asteroids = await self.controller.get_asteroids_by_earth_moid(
            self.session, max_moid
        )
        return [self._model_to_dict(a) for a in asteroids]
    
    async def get_by_orbit_class(self, orbit_class: str) -> List[Dict[str, Any]]:
        """
        Получение астероидов по классу орбиты.
        """
        asteroids = await self.controller.get_asteroids_by_orbit_class(
            self.session, orbit_class
        )
        return [self._model_to_dict(a) for a in asteroids]
    
    async def get_with_accurate_diameter(self) -> List[Dict[str, Any]]:
        """
        Получение астероидов с точными данными о диаметре.
        """
        asteroids = await self.controller.get_asteroids_with_accurate_diameter(
            self.session
        )
        return [self._model_to_dict(a) for a in asteroids]