"""
Контроллер для работы с данными о сближениях астероидов с Землей.
Использует общие методы BaseController.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, and_
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
    
    async def get_closest_approaches(
        self, 
        session: AsyncSession, 
        limit: int = 10
    ) -> List[CloseApproachModel]:
        """
        Получает ближайшие по времени сближения.
        """
        now = datetime.now()
        
        return await self.filter(
            session=session,
            filters={"approach_time__ge": now},
            limit=limit,
            order_by="approach_time"
        )
    
    async def get_closest_by_distance(
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
    
    async def get_approaches_with_threats(
        self,
        session: AsyncSession,
        threat_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CloseApproachModel]:
        """
        Получает сближения с оценками угроз.
        """
        from models.threat_assessment import ThreatAssessmentModel
        
        try:
            query = (
                select(self.model)
                .join(ThreatAssessmentModel, self.model.threat_assessment)
                .options(joinedload(self.model.threat_assessment))  # Используем joinedload
            )
            
            # Собираем условия
            conditions = []
            
            if threat_level:
                conditions.append(ThreatAssessmentModel.threat_level == threat_level)
            
            if start_date:
                conditions.append(self.model.approach_time >= start_date)
            
            if end_date:
                conditions.append(self.model.approach_time <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(self.model.approach_time).offset(skip).limit(limit)
            
            result = await session.execute(query)
            return result.unique().scalars().all()  # Используем unique() для избежания дубликатов
            
        except Exception as e:
            logger.error(f"Ошибка получения сближений с оценками угроз: {e}")
            raise