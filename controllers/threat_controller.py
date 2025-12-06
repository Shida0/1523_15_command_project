"""
Контроллер для работы с оценками угроз сближений.
Содержит методы для получения статистики по угрозам,
фильтрации по уровню опасности и массовых операций.
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
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            approach_id: ID сближения
            
        Returns:
            Оценка угрозы или None, если не найдена
        """
        try:
            query = select(self.model).where(self.model.approach_id == approach_id)
            result = await session.execute(query)
            threat = result.scalar_one_or_none()
            
            if threat:
                logger.debug(f"Найдена оценка угрозы для сближения ID {approach_id}")
            else:
                logger.debug(f"Оценка угрозы для сближения ID {approach_id} не найдена")
                
            return threat
            
        except Exception as e:
            logger.error(f"Ошибка получения оценки угрозы для сближения ID {approach_id}: {e}")
            raise
    
    async def get_high_threats(
        self, 
        session: AsyncSession, 
        limit: int = 20
    ) -> List[ThreatAssessmentModel]:
        """
        Получает сближения с высоким уровнем угрозы.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            limit: Максимальное количество записей
            
        Returns:
            Список оценок с высоким уровнем угрозы
        """
        try:
            query = (
                select(self.model)
                .where(
                    self.model.threat_level.in_(['высокий', 'критический'])
                )
                .order_by(desc(self.model.energy_megatons))
                .limit(limit)
            )
            
            result = await session.execute(query)
            threats = result.scalars().all()
            
            logger.debug(f"Получено {len(threats)} оценок с высоким уровнем угрозы")
            return threats
            
        except Exception as e:
            logger.error(f"Ошибка получения высоких угроз: {e}")
            raise
    
    async def update_assessment(
        self,
        session: AsyncSession,
        approach_id: int,
        new_data: Dict[str, Any]
    ) -> Optional[ThreatAssessmentModel]:
        """
        Обновляет оценку угрозы для сближения.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            approach_id: ID сближения
            new_data: Новые данные для оценки
            
        Returns:
            Обновленная оценка угрозы или None, если не найдена
        """
        try:
            # Находим существующую оценку
            threat = await self.get_by_approach_id(session, approach_id)
            
            if not threat:
                logger.warning(f"Попытка обновления несуществующей оценки для сближения ID {approach_id}")
                return None
            
            # Обновляем данные 
            threat = await self.update(session, threat.id, new_data)
            
            # Пересчитываем хеш входных данных
            threat.calculation_input_hash = None  # Будет пересчитан в __init__
            
            logger.info(f"Обновлена оценка угрозы для сближения ID {approach_id}")
            return threat
            
        except Exception as e:
            logger.error(f"Ошибка обновления оценки для сближения ID {approach_id}: {e}")
            await session.rollback()
            raise
    
    async def bulk_create_assessments(
        self,
        session: AsyncSession,
        assessments_data: List[Dict[str, Any]]
    ) -> int:
        """
        Массовое создание оценок угроз.
        Используется при ежедневном обновлении данных.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            assessments_data: Список словарей с данными оценок
            
        Returns:
            Количество созданных/обновленных оценок
        """
        created_updated = 0
        
        try:
            for assessment_data in assessments_data:
                approach_id = assessment_data.get('approach_id')
                
                if not approach_id:
                    logger.warning("Пропущена оценка без approach_id")
                    continue
                
                # Проверяем существование оценки
                existing = await self.get_by_approach_id(session, approach_id)
                
                if existing:
                    # Обновляем существующую оценку
                    await self.update_assessment(session, approach_id, assessment_data)
                else:
                    # Создаем новую оценку
                    await self.create(session, assessment_data)
                
                created_updated += 1
            
            await session.commit()
            logger.info(f"Массовое создание оценок завершено. Обработано: {created_updated}")
            return created_updated
            
        except Exception as e:
            logger.error(f"Ошибка массового создания оценок: {e}")
            await session.rollback()
            raise
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по оценкам угроз.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            
        Returns:
            Словарь со статистикой
        """
        try:
            # Общее количество оценок
            total_query = select(func.count()).select_from(self.model)
            total_result = await session.execute(total_query)
            total = total_result.scalar() or 0
            
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
            
            statistics = {
                "total_assessments": total,
                "threat_levels": level_stats,
                "average_energy_mt": avg_energy,
                "max_energy_mt": max_energy,
                "high_threat_count": (
                    level_stats.get('высокий', {}).get('count', 0) +
                    level_stats.get('критический', {}).get('count', 0)
                )
            }
            
            logger.debug(f"Статистика оценок угроз: {statistics}")
            return statistics
            
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
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            asteroid_id: ID астероида
            
        Returns:
            Список оценок угроз астероида
        """
        try:
            from models.close_approach import CloseApproachModel
            
            query = (
                select(self.model)
                .join(CloseApproachModel)
                .where(CloseApproachModel.asteroid_id == asteroid_id)
                .order_by(CloseApproachModel.approach_time)
            )
            
            result = await session.execute(query)
            threats = result.scalars().all()
            
            logger.debug(f"Получено {len(threats)} оценок угроз для астероида ID {asteroid_id}")
            return threats
            
        except Exception as e:
            logger.error(f"Ошибка получения оценок угроз для астероида ID {asteroid_id}: {e}")
            raise