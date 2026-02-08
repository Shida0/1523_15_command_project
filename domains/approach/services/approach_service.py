"""
Сервис для работы со сближениями.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from shared.infrastructure.services.base_service import BaseService
from domains.approach.models.close_approach import CloseApproachModel

logger = logging.getLogger(__name__)


class ApproachService(BaseService):
    """
    🌍 Сервис для работы со сближениями астероидов с Землей.

    Этот класс предоставляет методы для получения информации о сближениях астероидов с Землей,
    фильтрации по различным критериям и получения статистики.
    Наследуется от BaseService для общих CRUD операций.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """
        Инициализация сервиса для сближений.

        Args:
            session_factory: Фабрика для создания сессий SQLAlchemy
        """
        super().__init__(session_factory, CloseApproachModel)

    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===

    async def get_upcoming(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        📅 Получение ближайших сближений астероидов с Землей.

        Метод возвращает сближения, отсортированные по времени (ближайшие первыми).

        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)

        Returns:
            List[Dict[str, Any]]: Список ближайших сближений

        Example:
            >>> service = ApproachService(session_factory)
            >>> upcoming = await service.get_upcoming(5)
            >>> print(f"Ближайшие 5 сближений: {len(upcoming)}")
        """
        async with self.session_factory() as session:
            from shared.transaction.uow import UnitOfWork
            async with UnitOfWork(self.session_factory) as uow:
                approaches = await uow.approach_repo.get_upcoming_approaches(limit)
                return [self._model_to_dict(a) for a in approaches]

    async def get_closest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        📏 Получение самых близких по расстоянию сближений.

        Метод возвращает сближения, отсортированные по расстоянию (самые близкие первыми).

        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)

        Returns:
            List[Dict[str, Any]]: Список сближений, отсортированных по расстоянию

        Example:
            >>> service = ApproachService(session_factory)
            >>> closest = await service.get_closest(5)
            >>> print(f"Самые близкие 5 сближений: {len(closest)}")
        """
        async with self.session_factory() as session:
            from shared.transaction.uow import UnitOfWork
            async with UnitOfWork(self.session_factory) as uow:
                approaches = await uow.approach_repo.get_closest_approaches_by_distance(limit)
                return [self._model_to_dict(a) for a in approaches]

    async def get_fastest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ⚡ Получение сближений с наибольшей скоростью.

        Метод возвращает сближения, отсортированные по скорости (самые быстрые первыми).

        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)

        Returns:
            List[Dict[str, Any]]: Список сближений, отсортированных по скорости

        Example:
            >>> service = ApproachService(session_factory)
            >>> fastest = await service.get_fastest(5)
            >>> print(f"Самые быстрые 5 сближений: {len(fastest)}")
        """
        async with self.session_factory() as session:
            from shared.transaction.uow import UnitOfWork
            async with UnitOfWork(self.session_factory) as uow:
                approaches = await uow.approach_repo.get_fastest_approaches(limit)
                return [self._model_to_dict(a) for a in approaches]

    async def get_by_asteroid_id(self, asteroid_id: int) -> List[Dict[str, Any]]:
        """
        🔍 Получение всех сближений для астероида по его ID.

        Args:
            asteroid_id (int): Уникальный идентификатор астероида

        Returns:
            List[Dict[str, Any]]: Список всех сближений для указанного астероида

        Example:
            >>> service = ApproachService(session_factory)
            >>> approaches = await service.get_by_asteroid_id(123)
            >>> print(f"Сближения для астероида 123: {len(approaches)}")
        """
        async with self.session_factory() as session:
            from shared.transaction.uow import UnitOfWork
            async with UnitOfWork(self.session_factory) as uow:
                approaches = await uow.approach_repo.get_by_asteroid(asteroid_id)
                return [self._model_to_dict(a) for a in approaches]

    async def get_by_asteroid_designation(self, designation: str) -> List[Dict[str, Any]]:
        """
        🔍 Получение всех сближений для астероида по его обозначению NASA.

        Args:
            designation (str): Обозначение астероида в системе NASA

        Returns:
            List[Dict[str, Any]]: Список всех сближений для астероида с указанным обозначением

        Example:
            >>> service = ApproachService(session_factory)
            >>> approaches = await service.get_by_asteroid_designation("433")
            >>> print(f"Сближения для астероида 433: {len(approaches)}")
        """
        async with self.session_factory() as session:
            from shared.transaction.uow import UnitOfWork
            async with UnitOfWork(self.session_factory) as uow:
                approaches = await uow.approach_repo.get_by_asteroid_designation(designation)
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
        async with self.session_factory() as session:
            from shared.transaction.uow import UnitOfWork
            async with UnitOfWork(self.session_factory) as uow:
                return await uow.approach_repo.get_statistics()