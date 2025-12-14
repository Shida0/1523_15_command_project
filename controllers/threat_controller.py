"""
Контроллер для работы с оценками угроз сближений.
Использует общие методы BaseController.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import logging

from models.threat_assessment import ThreatAssessmentModel
from controllers.base_controller import BaseController

logger = logging.getLogger(__name__)


class ThreatController(BaseController[ThreatAssessmentModel]):
    """Контроллер для операций с оценками угроз."""
    
    
    def __init__(self):
        """Инициализирует контроллер для модели ThreatAssessmentModel."""
        super().__init__(ThreatAssessmentModel)
        logger.info("Инициализирован ThreatController")
    
    async def get_by_approach_id(
        self, 
        session: AsyncSession, 
        approach_id: int
    ) -> Optional[ThreatAssessmentModel]:
        """
        Получает оценку угрозы для конкретного сближения.
        """
        return await self._find_by_fields(session, {"approach_id": approach_id})
    
    async def get_high_threats(
        self, 
        session: AsyncSession, 
        limit: int = 20
    ) -> List[ThreatAssessmentModel]:
        """
        Получает сближения с высоким уровнем угрозы.
        """
        return await self.filter(
            session=session,
            filters={"threat_level__in": ["высокий", "критический"]},
            limit=limit,
            order_by="energy_megatons",
            order_desc=True
        )
    
    async def update_assessment(
        self,
        session: AsyncSession,
        approach_id: int,
        new_data: Dict[str, Any]
    ) -> Optional[ThreatAssessmentModel]:
        """
        Обновляет оценку угрозы для сближения.
        """
        threat = await self.get_by_approach_id(session, approach_id)
        
        if not threat:
            logger.warning(f"Попытка обновления несуществующей оценки для сближения ID {approach_id}")
            return None
        
        threat = await self.update(session, threat.id, new_data)
        
        # Пересчитываем хеш входных данных
        if threat:
            threat.calculation_input_hash = threat._calculate_input_hash()
            await session.flush()
        
        return threat
    
    async def bulk_create_assessments(
        self,
        session: AsyncSession,
        assessments_data: List[Dict[str, Any]]
    ) -> int:
        """
        Массовое создание оценок угроз.
        """
        created, updated = await self.bulk_create(
            session=session,
            data_list=assessments_data,
            conflict_action="update",
            conflict_fields=["approach_id"]  # Уникальное поле
        )
        
        return created + updated
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по оценкам угроз.
        """
        try:
            total = await self.count(session)
            
            # Распределение по уровням угроз
            threat_levels = ['низкий', 'средний', 'высокий', 'критический']
            level_stats = {}
            
            for level in threat_levels:
                level_query = select(func.count()).where(self.model.threat_level == level)
                level_result = await session.execute(level_query)
                count = level_result.scalar() or 0
                percent = round((count / total * 100) if total > 0 else 0, 1)
                level_stats[level] = {'count': count, 'percent': percent}
            
            # Средняя энергия
            avg_energy_query = select(func.avg(self.model.energy_megatons))
            avg_energy_result = await session.execute(avg_energy_query)
            avg_energy = round(avg_energy_result.scalar() or 0, 1)
            
            # Максимальная энергия
            max_energy_query = select(func.max(self.model.energy_megatons))
            max_energy_result = await session.execute(max_energy_query)
            max_energy = max_energy_result.scalar() or 0
            
            return {
                "total_assessments": total,
                "threat_levels": level_stats,
                "average_energy_mt": avg_energy,
                "max_energy_mt": max_energy,
                "high_threat_count": (
                    level_stats.get('высокий', {}).get('count', 0) +
                    level_stats.get('критический', {}).get('count', 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики оценок угроз: {e}")
            raise
    
    async def get_threats_by_asteroid(
        self,
        session: AsyncSession,
        asteroid_id: int
    ) -> List[ThreatAssessmentModel]:
        """
        Получает все оценки угроз для конкретного астероида.
        """
        from models.close_approach import CloseApproachModel
        
        query = (
            select(self.model)
            .join(CloseApproachModel)
            .where(CloseApproachModel.asteroid_id == asteroid_id)
            .order_by(CloseApproachModel.approach_time)
        )
        
        result = await session.execute(query)
        return result.scalars().all()