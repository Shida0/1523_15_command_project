from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from shared.infrastructure.services.base_service import BaseService
from domains.threat import ThreatAssessmentModel, ThreatRepository
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ThreatService(BaseService):
    """Сервис для работы с оценками угроз астероидов"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, ThreatAssessmentModel)

    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """Получение оценки угрозы по обозначению астероида"""
        async with UnitOfWork(self.session_factory) as uow:
            threat = await uow.threat_repo.get_by_designation(designation)
            return self._model_to_dict(threat) if threat else None

    async def get_by_asteroid_id(self, asteroid_id: int) -> Optional[Dict[str, Any]]:
        """Получение оценки угрозы для астероида по его ID"""
        async with UnitOfWork(self.session_factory) as uow:
            threat = await uow.threat_repo.get_by_asteroid_id(asteroid_id)
            return self._model_to_dict(threat) if threat else None

    async def get_high_risk(self, limit: Optional[int] = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Получение угроз с высоким уровнем риска (туринская шкала >= 5)"""
        return await self.filter({"ts_max__ge": 5}, skip, limit or 100, order_by="ts_max", order_desc=True)

    async def get_by_risk_level(self, min_ts: int = 0, max_ts: int = 10, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение угроз по диапазону значений Туринской шкалы"""
        filters = {"ts_max__ge": min_ts, "ts_max__le": max_ts}
        return await self.filter(filters, skip, limit or 100, order_by="ts_max", order_desc=True)

    async def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по оценкам угроз астероидов"""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.threat_repo.get_statistics()

    async def get_by_probability(self, min_probability: float = 0.0, max_probability: float = 1.0, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение угроз по диапазону вероятности столкновения"""
        filters = {"ip__ge": min_probability, "ip__le": max_probability}
        return await self.filter(filters, skip, limit or 100, order_by="ip", order_desc=True)

    async def get_by_energy(self, min_energy: float = 0.0, max_energy: Optional[float] = None, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение угроз по диапазону энергии воздействия"""
        filters = {"energy_megatons__ge": min_energy}
        if max_energy is not None:
            filters["energy_megatons__le"] = max_energy
        return await self.filter(filters, skip, limit or 100, order_by="energy_megatons", order_desc=True)

    async def get_by_category(self, category: str, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение угроз по категории воздействия"""
        return await self.filter({"impact_category": category}, skip, limit or 100, order_by="energy_megatons", order_desc=True)

    async def delete_threats_not_in_designations(self, designations: List[str]) -> int:
        """Удаляет угрозы, которых нет в списке NASA"""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.threat_repo.delete_threats_not_in_designations(designations)

    async def delete_threats_with_expired_years(self, current_year: int) -> int:
        """Удаляет угрозы у которых все года риска в прошлом"""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.threat_repo.delete_threats_with_expired_years(current_year)
