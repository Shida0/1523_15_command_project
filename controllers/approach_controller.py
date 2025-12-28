"""
Контроллер для работы с данными о сближениях астероидов с Землей.
Использует общие методы BaseController.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging

from models.close_approach import CloseApproachModel
from controllers.base_controller import BaseController

logger = logging.getLogger(__name__)


class ApproachController(BaseController[CloseApproachModel]):
    """Контроллер для операций со сближениями астероидов."""
    
    def __init__(self):
        """Инициализирует контроллер для модели CloseApproachModel."""
        super().__init__(CloseApproachModel)
        logger.info("Инициализирован ApproachController")
    
    async def get_by_asteroid(
        self, 
        session: AsyncSession, 
        asteroid_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает все сближения для конкретного астероида.
        """
        return await self.filter(
            session=session,
            filters={"asteroid_id": asteroid_id},
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_by_asteroid_designation(
        self,
        session: AsyncSession,
        designation: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает все сближения для астероида с указанным обозначением.
        """
        return await self.filter(
            session=session,
            filters={"asteroid_designation": designation},
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_approaches_in_period(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        max_distance: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает сближения в указанном временном периоде.
        """
        filters = {
            "approach_time__ge": start_date,
            "approach_time__le": end_date
        }
        
        if max_distance is not None:
            filters["distance_au__le"] = max_distance
        
        return await self.filter(
            session=session,
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_upcoming_approaches(
        self, 
        session: AsyncSession, 
        limit: int = 10
    ) -> List[CloseApproachModel]:
        """
        Получает ближайшие по времени сближения.
        """
        now = datetime.now(timezone.utc)
        
        return await self.filter(
            session=session,
            filters={"approach_time__ge": now},
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_closest_approaches_by_distance(
        self, 
        session: AsyncSession, 
        limit: int = 10
    ) -> List[CloseApproachModel]:
        """
        Получает самые близкие по расстоянию сближения.
        """
        return await self.filter(
            session=session,
            filters={},
            limit=limit,
            order_by="distance_au"
        )
    
    async def get_fastest_approaches(
        self,
        session: AsyncSession,
        limit: int = 10
    ) -> List[CloseApproachModel]:
        """
        Получает сближения с наибольшей скоростью.
        """
        return await self.filter(
            session=session,
            filters={},
            limit=limit,
            order_by="velocity_km_s",
            order_desc=True
        )
    
    async def bulk_create_approaches(
        self,
        session: AsyncSession,
        approaches_data: List[Dict[str, Any]],
        calculation_batch_id: str
    ) -> int:
        """
        Массовое создание сближений.
        """
        # Добавляем batch_id к каждому элементу
        for data in approaches_data:
            data['calculation_batch_id'] = calculation_batch_id
        
        # Используем общий bulk_create с проверкой по уникальным полям
        created, updated = await self.bulk_create(
            session=session,
            data_list=approaches_data,
            conflict_action="update",
            conflict_fields=["asteroid_id", "approach_time"]  # Уникальная комбинация
        )
        
        return created + updated
    
    async def delete_old_approaches(
        self, 
        session: AsyncSession, 
        cutoff_date: datetime
    ) -> int:
        """
        Удаляет устаревшие сближения (которые уже произошли).
        """
        return await self.bulk_delete(
            session=session,
            filters={"approach_time__lt": cutoff_date}
        )
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по сближениям.
        """
        try:
            # Общее количество
            total = await self.count(session)
            
            # Количество будущих сближений
            now = datetime.now(timezone.utc)
            future_query = select(func.count()).where(self.model.approach_time >= now)
            future_result = await session.execute(future_query)
            future_count = future_result.scalar() or 0
            
            # Среднее расстояние
            avg_distance_query = select(func.avg(self.model.distance_au))
            avg_distance_result = await session.execute(avg_distance_query)
            avg_distance_au = round(avg_distance_result.scalar() or 0, 6)
            
            # Средняя скорость
            avg_velocity_query = select(func.avg(self.model.velocity_km_s))
            avg_velocity_result = await session.execute(avg_velocity_query)
            avg_velocity = round(avg_velocity_result.scalar() or 0, 2)
            
            # Ближайшее сближение
            closest_query = select(func.min(self.model.distance_au))
            closest_result = await session.execute(closest_query)
            closest_au = closest_result.scalar() or 0
            
            return {
                "total_approaches": total,
                "future_approaches": future_count,
                "past_approaches": total - future_count,
                "average_distance_au": avg_distance_au,
                "average_velocity_km_s": avg_velocity,
                "closest_distance_au": closest_au,
                "closest_distance_km": closest_au * 149597870.7,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики сближений: {e}")
            raise