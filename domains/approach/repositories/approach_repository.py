# -*- coding: utf-8 -*-
"""
Репозиторий для работы с данными о сближениях астероидов с Землей.
Использует общие методы BaseController.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from domains.approach.models.close_approach import CloseApproachModel
from shared.infrastructure import BaseRepository
from shared.utils.datetime_utils import now_aware

logger = logging.getLogger(__name__)

class ApproachRepository(BaseRepository[CloseApproachModel]):
    """Репозиторий для операций со сближениями астероидов."""

    def __init__(self):
        """Инициализирует репозиторий для модели CloseApproachModel."""
        super().__init__(CloseApproachModel)
        logger.info("Инициализирован ApproachRepository")
    
    async def get_by_asteroid(
        self,
        asteroid_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает все сближения для конкретного астероида.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"asteroid_id": asteroid_id},
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_by_asteroid_designation(
        self,
        designation: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает все сближения для астероида с указанным обозначением.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"asteroid_designation": designation},
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_approaches_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        max_distance: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает сближения в указанном временном периоде.
        Без коммита (чтение).
        """
        # Ensure datetime objects are timezone-aware
        from shared.utils.datetime_utils import to_aware
        start_date = to_aware(start_date)
        end_date = to_aware(end_date)
        
        filters = {
            "approach_time__ge": start_date,
            "approach_time__le": end_date
        }

        if max_distance is not None:
            filters["distance_au__le"] = max_distance

        return await self.filter(
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_upcoming_approaches(
        self,
        limit: int = 10,
        skip: int = 0
    ) -> List[CloseApproachModel]:
        """
        Получает ближайшие по времени сближения.
        Без коммита (чтение).
        """
        now = now_aware()

        return await self.filter(
            filters={"approach_time__ge": now},
            skip=skip,
            limit=limit,
            order_by="approach_time"
        )

    async def get_closest_approaches_by_distance(
        self,
        limit: int = 10,
        skip: int = 0
    ) -> List[CloseApproachModel]:
        """
        Получает самые близкие по расстоянию сближения.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={},
            skip=skip,
            limit=limit,
            order_by="distance_au"
        )

    async def get_fastest_approaches(
        self,
        limit: int = 10,
        skip: int = 0
    ) -> List[CloseApproachModel]:
        """
        Получает сближения с наибольшей скоростью.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={},
            skip=skip,
            limit=limit,
            order_by="velocity_km_s",
            order_desc=True
        )
    
    async def bulk_create_approaches(
        self,
        approaches_data: List[Dict[str, Any]],
        calculation_batch_id: str
    ) -> int:
        """
        Массовое создание сближений с коммитом.
        """
        # Добавляем batch_id к каждому элементу
        for data in approaches_data:
            data['calculation_batch_id'] = calculation_batch_id

        # Используем общий bulk_create с проверкой по уникальным полям
        created, updated = await self.bulk_create(
            data_list=approaches_data,
            conflict_action="update",
            conflict_fields=["asteroid_id", "approach_time"]  # Уникальная комбинация
        )

        return created + updated
    
    async def delete_old_approaches(
        self,
        cutoff_date: datetime
    ) -> int:
        """
        Удаляет устаревшие сближения (которые уже произошли) с коммитом.
        """
        from shared.utils.datetime_utils import to_aware
        cutoff_date = to_aware(cutoff_date)
        
        return await self.bulk_delete(
            filters={"approach_time__lt": cutoff_date}
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по сближениям.
        Без коммита (чтение).
        """
        try:
            # Общее количество
            total = await self.count()

            # Количество будущих сближений
            now = now_aware()
            future_query = select(func.count()).where(self.model.approach_time >= now)
            future_result = await self.session.execute(future_query)
            future_scalar = future_result.scalar()
            # Handle case where scalar returns a coroutine (in test environment with improper mocks)
            if hasattr(future_scalar, '__await__'):
                future_count = await future_scalar or 0
            else:
                future_count = future_scalar or 0

            # Среднее расстояние
            avg_distance_query = select(func.avg(self.model.distance_au))
            avg_distance_result = await self.session.execute(avg_distance_query)
            avg_distance_scalar = avg_distance_result.scalar()
            # Handle case where scalar returns a coroutine (in test environment with improper mocks)
            if hasattr(avg_distance_scalar, '__await__'):
                avg_distance_raw = await avg_distance_scalar or 0
            else:
                avg_distance_raw = avg_distance_scalar or 0
            avg_distance_au = round(avg_distance_raw, 6)

            # Средняя скорость
            avg_velocity_query = select(func.avg(self.model.velocity_km_s))
            avg_velocity_result = await self.session.execute(avg_velocity_query)
            avg_velocity_scalar = avg_velocity_result.scalar()
            # Handle case where scalar returns a coroutine (in test environment with improper mocks)
            if hasattr(avg_velocity_scalar, '__await__'):
                avg_velocity_raw = await avg_velocity_scalar or 0
            else:
                avg_velocity_raw = avg_velocity_scalar or 0
            avg_velocity = round(avg_velocity_raw, 2)

            # Ближайшее сближение
            closest_query = select(func.min(self.model.distance_au))
            closest_result = await self.session.execute(closest_query)
            closest_scalar = closest_result.scalar()
            # Handle case where scalar returns a coroutine (in test environment with improper mocks)
            if hasattr(closest_scalar, '__await__'):
                closest_raw = await closest_scalar or 0
            else:
                closest_raw = closest_scalar or 0
            closest_au = closest_raw or 0

            return {
                "total_approaches": total,
                "future_approaches": future_count,
                "past_approaches": total - future_count,
                "average_distance_au": avg_distance_au,
                "average_velocity_km_s": avg_velocity,
                "closest_distance_au": closest_au,
                "closest_distance_km": closest_au * 149597870.7,
                "last_updated": now_aware().isoformat()
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики сближений: {e}")
            raise
        
    async def _safe_scalar_result(self, result):
        """
        Safely extract scalar result, handling both real results and mock coroutines.
        """
        scalar_value = result.scalar()
        # If scalar_value is a coroutine (from mock), await it
        if hasattr(scalar_value, '__await__'):
            return await scalar_value
        return scalar_value
        
