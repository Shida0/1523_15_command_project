"""
Сервис для работы с оценками угроз.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from controllers.threat_controller import ThreatController
from .base_service import BaseService

logger = logging.getLogger(__name__)


class ThreatService(BaseService):
    """
    Сервис для работы с оценками угроз.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса для угроз.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        controller = ThreatController()
        super().__init__(session, controller)
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===
    
    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """
        Получение оценки угрозы по обозначению астероида.
        """
        threat = await self.controller.get_by_designation(self.session, designation)
        return self._model_to_dict(threat) if threat else None
    
    async def get_by_asteroid_id(self, asteroid_id: int) -> List[Dict[str, Any]]:
        """
        Получение всех оценок угроз для астероида.
        """
        threats = await self.controller.get_threats_by_asteroid_id(
            self.session, asteroid_id
        )
        return [self._model_to_dict(t) for t in threats]
    
    async def get_high_risk(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Получение угроз с высоким уровнем риска (ts_max >= 5).
        """
        threats = await self.controller.get_high_risk_threats(self.session, limit)
        return [self._model_to_dict(t) for t in threats]
    
    async def get_by_risk_level(
        self, 
        min_ts: int = 0, 
        max_ts: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получение угроз по диапазону значений Туринской шкалы.
        """
        threats = await self.controller.get_threats_by_risk_level(
            self.session, min_ts, max_ts
        )
        return [self._model_to_dict(t) for t in threats]
    
    async def get_by_energy(
        self, 
        min_energy: float = 0.0,
        max_energy: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение угроз по диапазону энергии воздействия.
        """
        threats = await self.controller.get_threats_by_energy(
            self.session, min_energy, max_energy
        )
        return [self._model_to_dict(t) for t in threats]
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Получение угроз по категории воздействия.
        """
        threats = await self.controller.get_threats_by_impact_category(
            self.session, category
        )
        return [self._model_to_dict(t) for t in threats]