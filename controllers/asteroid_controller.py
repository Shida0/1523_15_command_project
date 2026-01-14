"""
Контроллер для работы с астероидами.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import logging

from models.asteroid import AsteroidModel
from .base_controller import BaseController

logger = logging.getLogger(__name__)


class AsteroidController(BaseController[AsteroidModel]):
    """Контроллер для операций с астероидами."""
    
    def __init__(self):
        """Инициализирует контроллер для модели AsteroidModel."""
        super().__init__(AsteroidModel)
        logger.info("Инициализирован AsteroidController")
    
    async def get_by_designation(self, session: AsyncSession, designation: str) -> Optional[AsteroidModel]:
        """
        Находит астероид по обозначению NASA.
        Без коммита (чтение).
        """
        return await self._find_by_fields(session, {"designation": designation})
    
    async def search_by_name_or_designation(
        self, 
        session: AsyncSession, 
        search_term: str,
        skip: int = 0, 
        limit: int = 50
    ) -> List[AsteroidModel]:
        """
        Ищет астероиды по названию или обозначению.
        Без коммита (чтение).
        """
        return await self.search(
            session=session,
            search_term=search_term,
            search_fields=["name", "designation"],
            skip=skip,
            limit=limit
        )
    
    async def get_asteroids_by_diameter_range(
        self,
        session: AsyncSession,
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
            session=session,
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="estimated_diameter_km"
        )
    
    async def get_asteroids_by_earth_moid(
        self,
        session: AsyncSession,
        max_moid: float,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает астероиды с MOID меньше указанного значения.
        Без коммита (чтение).
        """
        return await self.filter(
            session=session,
            filters={"earth_moid_au__le": max_moid},
            skip=skip,
            limit=limit,
            order_by="earth_moid_au"
        )
    
    async def get_asteroids_with_accurate_diameter(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает астероиды с точными данными о диаметре.
        Без коммита (чтение).
        """
        return await self.filter(
            session=session,
            filters={"accurate_diameter": True},
            skip=skip,
            limit=limit,
            order_by="estimated_diameter_km"
        )
    
    async def get_asteroids_by_orbit_class(
        self,
        session: AsyncSession,
        orbit_class: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает астероиды по классу орбиты.
        Без коммита (чтение).
        """
        return await self.filter(
            session=session,
            filters={"orbit_class": orbit_class},
            skip=skip,
            limit=limit,
            order_by="designation"
        )
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по астероидам.
        Без коммита (чтение).
        """
        try:
            # Общее количество
            total = await self.count(session)
            
            # Средний диаметр
            avg_diameter_query = select(func.avg(self.model.estimated_diameter_km))
            avg_diameter_result = await session.execute(avg_diameter_query)
            avg_diameter = round(avg_diameter_result.scalar() or 0, 2)
            
            # Минимальный MOID (самый опасный астероид)
            min_moid_query = select(func.min(self.model.earth_moid_au))
            min_moid_result = await session.execute(min_moid_query)
            min_moid = min_moid_result.scalar() or 0
            
            # Количество астероидов с точными диаметрами
            accurate_count_query = select(func.count()).where(self.model.accurate_diameter == True)
            accurate_count_result = await session.execute(accurate_count_query)
            accurate_count = accurate_count_result.scalar() or 0
            
            # Количество астероидов по источникам диаметра
            source_stats = {}
            for source in ['measured', 'computed', 'calculated']:
                source_query = select(func.count()).where(self.model.diameter_source == source)
                source_result = await session.execute(source_query)
                source_stats[source] = source_result.scalar() or 0
            
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
        session: AsyncSession,
        asteroids_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое создание астероидов с коммитом.
        """
        created, updated = await self.bulk_create(
            session=session,
            data_list=asteroids_data,
            conflict_action="update",
            conflict_fields=["designation"]  # Уникальное поле
        )
        
        return created, updated
    