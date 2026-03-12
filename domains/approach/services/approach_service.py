"""
Сервис для работы со сближениями.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from shared.infrastructure.services.base_service import BaseService
from domains.approach.models.close_approach import CloseApproachModel
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ApproachService(BaseService):
    """
    Сервис для работы со сближениями астероидов с Землей.
    Наследуется от BaseService для общих CRUD операций.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, CloseApproachModel)

    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===

    async def get_upcoming(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        📅 Получение ближайших сближений астероидов с Землей.
        Возвращает сближения, отсортированные по времени (ближайшие первыми).

        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)

        Returns:
            List[Dict[str, Any]]: Список ближайших сближений

        Example:
            >>> service = ApproachService(session_factory)
            >>> upcoming = await service.get_upcoming(5)
            >>> print(f"Ближайшие 5 сближений: {len(upcoming)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_upcoming_approaches(limit=limit, skip=skip)
            return [self._model_to_dict(a) for a in approaches]

    async def get_closest(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        📏 Получение самых близких по расстоянию сближений.
        Возвращает сближения, отсортированные по расстоянию (самые близкие первыми).

        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)

        Returns:
            List[Dict[str, Any]]: Список сближений, отсортированных по расстоянию

        Example:
            >>> service = ApproachService(session_factory)
            >>> closest = await service.get_closest(5)
            >>> print(f"Самые близкие 5 сближений: {len(closest)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_closest_approaches_by_distance(limit=limit, skip=skip)
            return [self._model_to_dict(a) for a in approaches]

    async def get_fastest(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        ⚡ Получение сближений с наибольшей скоростью.
        Возвращает сближения, отсортированные по скорости (самые быстрые первыми).

        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)

        Returns:
            List[Dict[str, Any]]: Список сближений, отсортированных по скорости

        Example:
            >>> service = ApproachService(session_factory)
            >>> fastest = await service.get_fastest(5)
            >>> print(f"Самые быстрые 5 сближений: {len(fastest)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_fastest_approaches(limit=limit, skip=skip)
            return [self._model_to_dict(a) for a in approaches]

    async def get_by_asteroid_id(
        self,
        asteroid_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        🔍 Получение всех сближений для астероида по его ID.

        Args:
            asteroid_id (int): Уникальный идентификатор астероида
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список всех сближений для указанного астероида

        Example:
            >>> service = ApproachService(session_factory)
            >>> approaches = await service.get_by_asteroid_id(123)
            >>> print(f"Сближения для астероида 123: {len(approaches)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_by_asteroid(
                asteroid_id, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in approaches]

    async def get_by_asteroid_designation(
        self,
        designation: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        🔍 Получение всех сближений для астероида по его обозначению NASA.

        Args:
            designation (str): Обозначение астероида в системе NASA
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список всех сближений для астероида с указанным обозначением

        Example:
            >>> service = ApproachService(session_factory)
            >>> approaches = await service.get_by_asteroid_designation("433")
            >>> print(f"Сближения для астероида 433: {len(approaches)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_by_asteroid_designation(
                designation, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in approaches]

    async def get_approaches_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        max_distance: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        📅 Получение сближений в указанном временном периоде.
        Возвращает сближения, произошедшие (или запланированные) в указанный
        временной период, с возможностью фильтрации по максимальному расстоянию.

        Args:
            start_date (datetime): Начало временного периода
            end_date (datetime): Конец временного периода
            max_distance (Optional[float]): Максимальное расстояние в а.е. для фильтрации (по умолчанию None)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список сближений в заданном временном периоде

        Example:
            >>> from datetime import datetime, timedelta
            >>> service = ApproachService(session_factory)
            >>> start = datetime.now()
            >>> end = start + timedelta(days=365)
            >>> approaches = await service.get_approaches_in_period(start, end, max_distance=0.05)
            >>> print(f"Сближения в следующем году в пределах 0.05 а.е.: {len(approaches)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_approaches_in_period(
                start_date, end_date, max_distance=max_distance, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in approaches]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        📈 Возвращает статистику по сближениям астероидов с Землей.
        Статистика включает:
        - Общее количество сближений
        - Среднее расстояние
        - Среднюю скорость
        - Минимальное и максимальное расстояния
        - Минимальную и максимальную скорости

        Returns:
            Dict[str, Any]: Словарь со статистическими данными о сближениях

        Example:
            >>> service = ApproachService(session_factory)
            >>> stats = await service.get_statistics()
            >>> print(f"Всего сближений: {stats['total_approaches']}")
            >>> print(f"Среднее расстояние: {stats['avg_distance_au']} а.е.")
        """
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.approach_repo.get_statistics()