"""
Сервис для работы со сближениями.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from controllers.approach_controller import ApproachController
from .base_service import BaseService

logger = logging.getLogger(__name__)


class ApproachService(BaseService):
    """
    Сервис для работы со сближениями.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса для сближений.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        controller = ApproachController()
        super().__init__(session, controller)
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===
    
    async def get_upcoming(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение ближайших сближений.
        """
        approaches = await self.controller.get_upcoming_approaches(
            self.session, limit
        )
        return [self._model_to_dict(a) for a in approaches]
    
    async def get_closest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение самых близких по расстоянию сближений.
        """
        approaches = await self.controller.get_closest_approaches_by_distance(
            self.session, limit
        )
        return [self._model_to_dict(a) for a in approaches]
    
    async def get_fastest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение сближений с наибольшей скоростью.
        """
        approaches = await self.controller.get_fastest_approaches(
            self.session, limit
        )
        return [self._model_to_dict(a) for a in approaches]
    
    async def get_by_asteroid_id(self, asteroid_id: int) -> List[Dict[str, Any]]:
        """
        Получение всех сближений для астероида.
        """
        approaches = await self.controller.get_by_asteroid(self.session, asteroid_id)
        return [self._model_to_dict(a) for a in approaches]
    
    async def get_by_asteroid_designation(self, designation: str) -> List[Dict[str, Any]]:
        """
        Получение всех сближений для астероида по обозначению.
        """
        approaches = await self.controller.get_by_asteroid_designation(
            self.session, designation
        )
        return [self._model_to_dict(a) for a in approaches]