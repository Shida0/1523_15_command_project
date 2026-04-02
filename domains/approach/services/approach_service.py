from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from shared.infrastructure.services.base_service import BaseService
from domains.approach import CloseApproachModel
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ApproachService(BaseService):
    """Сервис для работы со сближениями астероидов с Землей"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, CloseApproachModel)

    async def get_upcoming(self, limit: Optional[int] = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Получение ближайших сближений астероидов с Землей"""
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_upcoming_approaches(limit, skip)
            return [self._model_to_dict(a) for a in approaches]

    async def get_count(self) -> int:
        """Получение общего количества сближений"""
        return await super().count()

    async def get_closest(self, limit: Optional[int] = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Получение самых близких по расстоянию сближений"""
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_closest_approaches_by_distance(limit, skip)
            return [self._model_to_dict(a) for a in approaches]

    async def get_fastest(self, limit: Optional[int] = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Получение сближений с наибольшей скоростью"""
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_fastest_approaches(limit, skip)
            return [self._model_to_dict(a) for a in approaches]

    async def get_by_asteroid_id(self, asteroid_id: int, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение всех сближений для астероида по его ID"""
        return await self.filter({"asteroid_id": asteroid_id}, skip, limit or 100)

    async def get_by_asteroid_designation(self, designation: str, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение всех сближений для астероида по его обозначению NASA"""
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_by_asteroid_designation(designation, skip, limit)
            return [self._model_to_dict(a) for a in approaches]

    async def get_approaches_in_period(self, start_date: datetime, end_date: datetime, max_distance: Optional[float] = None, skip: int = 0, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """Получение сближений в указанном временном периоде"""
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_approaches_in_period(start_date, end_date, max_distance, skip, limit)
            return [self._model_to_dict(a) for a in approaches]

    async def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по сближениям астероидов с Землей"""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.approach_repo.get_statistics()

    async def delete_old_approaches(self, cutoff_date: datetime) -> int:
        """Удаляет старые сближения (которые уже произошли)"""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.approach_repo.delete_old_approaches(cutoff_date)
