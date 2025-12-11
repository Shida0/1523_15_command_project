"""
Контроллер для работы с данными о сближениях астероидов с Землей.
Содержит методы для работы с временными периодами, поиска ближайших сближений
и массовых операций для ежедневного обновления.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
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
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            asteroid_id: ID астероида
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список сближений астероида, отсортированных по дате
        """
        try:
            query = (
                select(self.model)
                .where(self.model.asteroid_id == asteroid_id)
                .order_by(self.model.approach_time)
                .offset(skip)
                .limit(limit)
            )
            
            result = await session.execute(query)
            approaches = result.scalars().all()
            
            logger.debug(f"Получено {len(approaches)} сближений для астероида ID {asteroid_id}")
            return approaches
            
        except Exception as e:
            logger.error(f"Ошибка получения сближений для астероида ID {asteroid_id}: {e}")
            raise
    
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
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            max_distance: Максимальное расстояние (а.е.), если нужна фильтрация
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список сближений в указанном периоде
        """
        try:
            query = (
                select(self.model)
                .where(
                    and_(
                        self.model.approach_time >= start_date,
                        self.model.approach_time <= end_date
                    )
                )
                .order_by(self.model.approach_time)
            )
            
            # Дополнительная фильтрация по расстоянию
            if max_distance is not None:
                query = query.where(self.model.distance_au <= max_distance)
            
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            approaches = result.scalars().all()
            
            logger.debug(
                f"Найдено {len(approaches)} сближений в период "
                f"{start_date.date()} - {end_date.date()}"
            )
            return approaches
            
        except Exception as e:
            logger.error(
                f"Ошибка получения сближений в период "
                f"{start_date.date()} - {end_date.date()}: {e}"
            )
            raise
    
    async def get_closest_approaches(
        self, 
        session: AsyncSession, 
        limit: int = 10
    ) -> List[CloseApproachModel]:
        """
        Получает ближайшие по времени сближения.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            limit: Количество ближайших сближений
            
        Returns:
            Список ближайших сближений
        """
        try:
            now = datetime.now(timezone.utc)
            
            query = (
                select(self.model)
                .where(self.model.approach_time >= now)
                .order_by(self.model.approach_time)
                .limit(limit)
            )
            
            result = await session.execute(query)
            approaches = result.scalars().all()
            
            logger.debug(f"Получено {len(approaches)} ближайших сближений")
            return approaches
            
        except Exception as e:
            logger.error(f"Ошибка получения ближайших сближений: {e}")
            raise
    
    async def get_closest_by_distance(
        self, 
        session: AsyncSession, 
        limit: int = 10
    ) -> List[CloseApproachModel]:
        """
        Получает самые близкие по расстоянию сближения.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            limit: Количество самых близких сближений
            
        Returns:
            Список самых близких сближений
        """
        try:
            query = (
                select(self.model)
                .order_by(self.model.distance_au)
                .limit(limit)
            )
            
            result = await session.execute(query)
            approaches = result.scalars().all()
            
            logger.debug(f"Получено {len(approaches)} самых близких сближений")
            return approaches
            
        except Exception as e:
            logger.error(f"Ошибка получения самых близких сближений: {e}")
            raise
    
    async def bulk_create_approaches(
        self,
        session: AsyncSession,
        approaches_data: List[Dict[str, Any]],
        calculation_batch_id: str
    ) -> int:
        """
        Массовое создание сближений.
        Используется при ежедневном обновлении данных.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            approaches_data: Список словарей с данными сближений
            calculation_batch_id: Идентификатор партии расчета - индентификатор по времени создания короче говоря
            
        Returns:
            Количество созданных записей
        """
        created = 0
        
        try:
            for approach_data in approaches_data:
                # Добавляем идентификатор партии
                approach_data['calculation_batch_id'] = calculation_batch_id
                
                # Проверяем, существует ли уже такое сближение
                asteroid_id = approach_data.get('asteroid_id')
                approach_time = approach_data.get('approach_time')
                
                if not asteroid_id or not approach_time:
                    logger.warning("Пропущено сближение без asteroid_id или approach_time")
                    continue
                
                # Проверяем уникальность сближения
                existing_query = select(self.model).where(
                    and_(
                        self.model.asteroid_id == asteroid_id,
                        self.model.approach_time == approach_time
                    )
                )
                existing_result = await session.execute(existing_query)
                existing = existing_result.scalar_one_or_none()
                
                if not existing:
                    # Создаем новое сближение
                    await self.create(session, approach_data)
                    created += 1
                else:
                    # Обновляем существующее сближение
                    await self.update(session, existing.id, approach_data)
            
            await session.commit()
            logger.info(f"Массовое создание сближений завершено. Создано/обновлено: {created}")
            return created
            
        except Exception as e:
            logger.error(f"Ошибка массового создания сближений: {e}")
            await session.rollback()
            raise
    
    async def delete_old_approaches(
        self, 
        session: AsyncSession, 
        cutoff_date: datetime
    ) -> int:
        """
        Удаляет устаревшие сближения (которые уже произошли).
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            cutoff_date: Дата, старше которой сближения удаляются
            
        Returns:
            Количество удаленных записей
        """
        try:
            # Находим сближения для удаления
            query = select(self.model).where(self.model.approach_time < cutoff_date)
            result = await session.execute(query)
            old_approaches = result.scalars().all()
            
            # Удаляем найденные сближения
            deleted_count = 0
            for approach in old_approaches:
                await session.delete(approach)
                deleted_count += 1
            
            await session.commit()
            
            logger.info(f"Удалено {deleted_count} устаревших сближений (до {cutoff_date.date()})")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка удаления устаревших сближений: {e}")
            await session.rollback()
            raise
    
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
        Получает сближения с оценками угрозы.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            threat_level: Уровень угрозы для фильтрации
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список сближений с загруженными оценками угроз
        """
        try:
            from models.threat_assessment import ThreatAssessmentModel
            
            query = (
                select(self.model)
                .join(ThreatAssessmentModel)
                .order_by(self.model.approach_time)
            )
            
            # Фильтрация по уровню угрозы
            if threat_level:
                query = query.where(ThreatAssessmentModel.threat_level == threat_level)
            
            # Фильтрация по дате
            if start_date:
                query = query.where(self.model.approach_time >= start_date)
            if end_date:
                query = query.where(self.model.approach_time <= end_date)
            
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            approaches = result.scalars().all()
            
            logger.debug(f"Получено {len(approaches)} сближений с оценками угроз")
            return approaches
            
        except Exception as e:
            logger.error(f"Ошибка получения сближений с оценками угроз: {e}")
            raise