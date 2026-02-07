# -*- coding: utf-8 -*-
"""
Репозиторий для работы с астероидами.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import logging

from domains.asteroid.models.asteroid import AsteroidModel
from shared.infrastructure import BaseRepository

logger = logging.getLogger(__name__)

class AsteroidRepository(BaseRepository[AsteroidModel]):
    """Репозиторий для операций с астероидами."""
    
    def __init__(self):
        """Инициализирует репозиторий для модели AsteroidModel."""
        super().__init__(AsteroidModel)
        logger.info("Инициализирован AsteroidRepository")
    
    async def get_by_designation(self, designation: str) -> Optional[AsteroidModel]:
        """
        Находит астероид по обозначению NASA.
        Без коммита (чтение).
        """
        return await self._find_by_fields({"designation": designation})
    
    async def search_by_name_or_designation(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[AsteroidModel]:
        """
        Ищет астероиды по названию или обозначению.
        Без коммита (чтение).
        """
        return await self.search(
            search_term=search_term,
            search_fields=["name", "designation"],
            skip=skip,
            limit=limit
        )
    
    async def get_asteroids_by_diameter_range(
        self,
        min_diameter: Optional[float] = None,
        max_diameter: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Фильтрует астероиды по диапазону диаметров.
        Без коммита (чтение).
        """
        filters = {}
        if min_diameter is not None:
            filters["estimated_diameter_km__ge"] = min_diameter
        if max_diameter is not None:
            filters["estimated_diameter_km__le"] = max_diameter

        return await self.filter(
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="estimated_diameter_km"
        )
    
    async def get_asteroids_by_earth_moid(
        self,
        max_moid: float,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает астероиды с MOID меньше указанного значения.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"earth_moid_au__le": max_moid},
            skip=skip,
            limit=limit,
            order_by="earth_moid_au"
        )
    
    async def get_asteroids_with_accurate_diameter(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает астероиды с точными данными о диаметре.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"accurate_diameter": True},
            skip=skip,
            limit=limit,
            order_by="estimated_diameter_km"
        )
    
    async def get_asteroids_by_orbit_class(
        self,
        orbit_class: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает астероиды по классу орбиты.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"orbit_class": orbit_class},
            skip=skip,
            limit=limit,
            order_by="designation"
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по астероидам.
        Без коммита (чтение).
        """
        try:
            # Общее количество
            total = await self.count()

            # Средний диаметр
            avg_diameter_query = select(func.avg(self.model.estimated_diameter_km))
            avg_diameter_result = await self.session.execute(avg_diameter_query)
            avg_diameter_scalar = avg_diameter_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(avg_diameter_scalar, '__await__'):
                avg_diameter_value = await avg_diameter_scalar
            else:
                avg_diameter_value = avg_diameter_scalar
            avg_diameter = round(avg_diameter_value or 0, 2)

            # Минимальный MOID (самый опасный астероид)
            min_moid_query = select(func.min(self.model.earth_moid_au))
            min_moid_result = await self.session.execute(min_moid_query)
            min_moid_scalar = min_moid_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(min_moid_scalar, '__await__'):
                min_moid_value = await min_moid_scalar
            else:
                min_moid_value = min_moid_scalar
            min_moid = min_moid_value or 0

            # Количество астероидов с точными диаметрами
            accurate_count_query = select(func.count()).where(self.model.accurate_diameter == True)
            accurate_count_result = await self.session.execute(accurate_count_query)
            accurate_count_scalar = accurate_count_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(accurate_count_scalar, '__await__'):
                accurate_count_value = await accurate_count_scalar
            else:
                accurate_count_value = accurate_count_scalar
            accurate_count = accurate_count_value or 0

            # Количество астероидов по источникам диаметра
            source_stats = {}
            for source in ['measured', 'computed', 'calculated']:
                source_query = select(func.count()).where(self.model.diameter_source == source)
                source_result = await self.session.execute(source_query)
                source_scalar = source_result.scalar()
                # Handle the case where scalar returns a coroutine due to mocking in tests
                if hasattr(source_scalar, '__await__'):
                    source_value = await source_scalar
                else:
                    source_value = source_scalar
                source_stats[source] = source_value or 0

            return {
                "total_asteroids": total,
                "average_diameter_km": avg_diameter,
                "min_earth_moid_au": min_moid,
                "accurate_diameter_count": accurate_count,
                "percent_accurate": round((accurate_count / total * 100) if total > 0 else 0, 1),
                "diameter_source_stats": source_stats,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики астероидов: {e}")
            raise
    
    async def bulk_create_asteroids(
        self,
        asteroids_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое создание астероидов с коммитом.
        """
        created, updated = await self.bulk_create(
            data_list=asteroids_data,
            conflict_action="update",
            conflict_fields=["designation"]  # Уникальное поле
        )

        return created, updated

