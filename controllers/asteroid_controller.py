"""
Контроллер для работы с данными астероидов.
Использует общие методы BaseController для устранения дублирования.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import logging

from models.asteroid import AsteroidModel
from controllers.base_controller import BaseController

logger = logging.getLogger(__name__)


class AsteroidController(BaseController[AsteroidModel]):
    """Контроллер для операций с астероидами."""
    
    def __init__(self):
        """Инициализирует контроллер для модели AsteroidModel."""
        super().__init__(AsteroidModel)
        logger.info("Инициализирован AsteroidController")
    
    async def get_by_mpc_number(self, session: AsyncSession, mpc_number: int) -> Optional[AsteroidModel]:
        """
        Находит астероид по номеру MPC.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            mpc_number: Уникальный номер из каталога MPC
            
        Returns:
            Объект AsteroidModel или None, если не найден
        """
        return await self._find_by_fields(session, {"mpc_number": mpc_number})
    
    async def get_pha_asteroids(
        self, 
        session: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AsteroidModel]:
        """
        Получает только потенциально опасные астероиды (PHA).
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список потенциально опасных астероидов
        """
        return await self.filter(
            session=session,
            filters={"is_pha": True},
            skip=skip,
            limit=limit,
            order_by="earth_moid_au"  # Сначала самые опасные
        )
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        search_term: str,
        skip: int = 0, 
        limit: int = 50
    ) -> List[AsteroidModel]:
        """
        Ищет астероиды по названию или обозначению.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            search_term: Строка для поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список найденных астероидов
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
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            min_diameter: Минимальный диаметр (км)
            max_diameter: Максимальный диаметр (км)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список отфильтрованных астероидов
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
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по астероидам.
        """
        try:
            # Общее количество
            total = await self.count(session)
            
            # Количество PHA
            pha_query = select(func.count()).select_from(self.model).where(self.model.is_pha == True)
            pha_result = await session.execute(pha_query)
            pha_count = pha_result.scalar() or 0
            
            # Средний диаметр
            avg_diameter_query = select(func.avg(self.model.estimated_diameter_km))
            avg_diameter_result = await session.execute(avg_diameter_query)
            avg_diameter = round(avg_diameter_result.scalar() or 0, 2)
            
            # Минимальный MOID (самый опасный астероид)
            min_moid_query = select(func.min(self.model.earth_moid_au))
            min_moid_result = await session.execute(min_moid_query)
            min_moid = min_moid_result.scalar() or 0
            
            return {
                "total_asteroids": total,
                "pha_count": pha_count,
                "percent_pha": round((pha_count / total * 100) if total > 0 else 0, 1),
                "average_diameter_km": avg_diameter,
                "min_moid_au": min_moid,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики астероидов: {e}")
            raise