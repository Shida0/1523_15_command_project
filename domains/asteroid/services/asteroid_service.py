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
    """
    Сервис для работы с астероидами.
    Наследуется от BaseService для общих CRUD операций.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, AsteroidModel)

    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===

    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """
        🎯 Получение астероида по обозначению NASA.

        Args:
            designation (str): Обозначение астероида в системе NASA

        Returns:
            Optional[Dict[str, Any]]: Словарь с данными об астероиде или None, если не найден

        Example:
            >>> service = AsteroidService(session_factory)
            >>> asteroid = await service.get_by_designation("433")
            >>> print(asteroid['name'])  # Выведет имя астероида
        """
        async with UnitOfWork(self.session_factory) as uow:
            asteroid = await uow.asteroid_repo.get_by_designation(designation)
            return self._model_to_dict(asteroid) if asteroid else None

    async def get_by_moid(
        self,
        max_moid: float = 0.05,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        🔍 Получение астероидов с MOID (минимальное расстояние пересечения орбит) меньше указанного.
        MOID (Minimum Orbit Intersection Distance) - это минимальное расстояние между
        орбитами двух тел. Для астероидов PHA (Potentially Hazardous Asteroids) MOID ≤ 0.05 а.е.

        Args:
            max_moid (float): Максимальное значение MOID для фильтрации (по умолчанию 0.05 а.е.)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список астероидов с MOID меньше указанного значения

        Example:
            >>> service = AsteroidService(session_factory)
            >>> nearby_asteroids = await service.get_by_moid(0.02)
            >>> print(f"Найдено {len(nearby_asteroids)} близких астероидов")
        """
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_asteroids_by_earth_moid(
                max_moid, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in asteroids]

    async def get_by_orbit_class(
        self,
        orbit_class: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        📊 Получение астероидов по классу орбиты.
        Поддерживаемые классы орбит:
        - Apollo: орбита пересекает орбиту Земли, большая полуось > 1 а.е.
        - Aten: орбита пересекает орбиту Земли, большая полуось < 1 а.е.
        - Amor: орбита расположена между орбитами Земли и Марса

        Args:
            orbit_class (str): Класс орбиты (например, "Apollo", "Aten", "Amor")
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список астероидов указанного класса орбиты

        Example:
            >>> service = AsteroidService(session_factory)
            >>> apollo_asteroids = await service.get_by_orbit_class("Apollo")
            >>> print(f"Найдено {len(apollo_asteroids)} астероидов класса Apollo")
        """
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_asteroids_by_orbit_class(
                orbit_class, skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in asteroids]

    async def get_with_accurate_diameter(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        📏 Получение астероидов с точными данными о диаметре.
        Астероиды с точными данными о диаметре имеют установленный флаг accurate_diameter=True.
        Эти данные обычно получены из прямых наблюдений, а не из расчетов.

        Args:
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список астероидов с точными данными о диаметре

        Example:
            >>> service = AsteroidService(session_factory)
            >>> accurate_diameter_asteroids = await service.get_with_accurate_diameter()
            >>> print(f"Найдено {len(accurate_diameter_asteroids)} астероидов с точными данными о диаметре")
        """
        async with UnitOfWork(self.session_factory) as uow:
            asteroids = await uow.asteroid_repo.get_asteroids_with_accurate_diameter(
                skip=skip, limit=limit
            )
            return [self._model_to_dict(a) for a in asteroids]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        📈 Возвращает статистику по астероидам.
        Статистика включает:
        - Общее количество астероидов
        - Средний диаметр
        - Минимальный MOID
        - Количество астероидов с точными диаметрами
        - Статистику по источникам данных о диаметрах

        Returns:
            Dict[str, Any]: Словарь со статистическими данными об астероидах

        Example:
            >>> service = AsteroidService(session_factory)
            >>> stats = await service.get_statistics()
            >>> print(f"Всего астероидов: {stats['total_asteroids']}")
            >>> print(f"Средний диаметр: {stats['average_diameter_km']} км")
        """
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.asteroid_repo.get_statistics()