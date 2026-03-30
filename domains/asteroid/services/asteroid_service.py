"""
Сервис для работы с астероидами.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from shared.infrastructure.services.base_service import BaseService
from domains.asteroid.models.asteroid import AsteroidModel
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class AsteroidService(BaseService):
    """Сервис для работы с астероидами."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, AsteroidModel)

    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """Получение астероида по обозначению NASA."""
        async with UnitOfWork(self.session_factory) as uow:
            asteroid = await uow.asteroid_repo.get_by_designation(designation)
            return self._model_to_dict(asteroid) if asteroid else None

    async def get_by_moid(
        self,
        max_moid: float = 0.05,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Получение астероидов с MOID меньше указанного."""
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_asteroids_by_earth_moid(
                max_moid, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in asteroids]

    async def get_all(
        self,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение всех астероидов с поддержкой пагинации.
        
        Args:
            skip: Количество пропускаемых записей.
            limit: Максимальное количество возвращаемых записей.
        
        Returns:
            Список всех астероидов в базе данных.
        """
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_all(skip=skip, limit=limit)
            return [self._model_to_dict(a) for a in asteroids]

    async def get_count(self, max_moid: float = 1.0) -> int:
        """Получение общего количества астероидов с MOID меньше указанного."""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.asteroid_repo.get_asteroids_count(max_moid)

    async def get_by_orbit_class(
        self,
        orbit_class: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Получение астероидов по классу орбиты."""
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_asteroids_by_orbit_class(
                orbit_class, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in asteroids]

    async def get_with_accurate_diameter(
        self,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Получение астероидов с точными данными о диаметре."""
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_asteroids_with_accurate_diameter(
                skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in asteroids]

    async def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по астероидам."""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.asteroid_repo.get_statistics()

    async def delete_asteroids_not_in_designations(
        self,
        designations: List[str]
    ) -> int:
        """Удаляет астероиды, которых нет в списке NASA."""
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.asteroid_repo.delete_asteroids_not_in_designations(designations)
