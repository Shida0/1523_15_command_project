"""
Контроллер для работы с данными астероидов.
Расширяет BaseController специфичными для астероидов операциями:
поиск по номеру MPC, фильтрация по опасности, массовое создание.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.sql import func
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
        try:
            query = select(self.model).where(self.model.mpc_number == mpc_number)
            result = await session.execute(query)
            asteroid = result.scalar_one_or_none()
            
            if asteroid:
                logger.debug(f"Найден астероид по номеру MPC {mpc_number}: {asteroid.name}")
            else:
                logger.debug(f"Астероид с номером MPC {mpc_number} не найден")
                
            return asteroid
            
        except Exception as e:
            logger.error(f"Ошибка поиска астероида по номеру MPC {mpc_number}: {e}")
            raise
    
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
        try:
            query = (
                select(self.model)
                .where(self.model.is_pha == True)
                .order_by(self.model.earth_moid_au)  # Сначала самые опасные
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(query)
            asteroids = result.scalars().all()
            
            logger.debug(f"Получено {len(asteroids)} потенциально опасных астероидов")
            return asteroids
            
        except Exception as e:
            logger.error(f"Ошибка получения PHA астероидов: {e}")
            raise
    
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
        try:
            search_pattern = f"%{search_term}%"
            
            query = (
                select(self.model)
                .where(
                    or_(
                        self.model.name.ilike(search_pattern),
                        self.model.designation.ilike(search_pattern)
                    )
                )
                .order_by(self.model.name)
                .offset(skip)
                .limit(limit)
            )
            
            result = await session.execute(query)
            asteroids = result.scalars().all()
            
            logger.debug(f"Поиск '{search_term}' вернул {len(asteroids)} астероидов")
            return asteroids
            
        except Exception as e:
            logger.error(f"Ошибка поиска астероидов по термину '{search_term}': {e}")
            raise
    
    async def bulk_create(
        self, 
        session: AsyncSession, 
        asteroids_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое создание астероидов.
        Используется при ежедневном обновлении данных.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            asteroids_data: Список словарей с данными астероидов
            
        Returns:
            Кортеж (создано, обновлено) - количество созданных и обновленных записей
        """
        created = 0
        updated = 0
        
        try:
            for asteroid_data in asteroids_data:
                mpc_number = asteroid_data.get('mpc_number')
                
                if not mpc_number:
                    logger.warning("Пропущен астероид без номера MPC")
                    continue
                
                # Проверяем существование астероида
                existing = await self.get_by_mpc_number(session, mpc_number)
                
                if existing:
                    # Обновляем существующий астероид
                    await self.update(session, existing.id, asteroid_data)
                    updated += 1
                else:
                    # Создаем новый астероид
                    await self.create(session, asteroid_data)
                    created += 1
            
            await session.commit()
            
            logger.info(f"Массовое создание завершено. Создано: {created}, Обновлено: {updated}")
            return created, updated
            
        except Exception as e:
            logger.error(f"Ошибка массового создания астероидов: {e}")
            await session.rollback()
            raise
    
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
        try:
            query = select(self.model)
            
            # Добавляем условия фильтрации
            conditions = []
            if min_diameter is not None:
                conditions.append(self.model.estimated_diameter_km >= min_diameter)
            if max_diameter is not None:
                conditions.append(self.model.estimated_diameter_km <= max_diameter)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Сортировка и пагинация
            query = query.order_by(self.model.estimated_diameter_km).offset(skip).limit(limit)
            
            result = await session.execute(query)
            asteroids = result.scalars().all()
            
            logger.debug(
                f"Фильтрация по диаметру "
                f"(min={min_diameter}, max={max_diameter}): найдено {len(asteroids)} астероидов"
            )
            return asteroids
            
        except Exception as e:
            logger.error(f"Ошибка фильтрации астероидов по диаметру: {e}")
            raise
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по астероидам.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            
        Returns:
            Словарь со статистикой
        """
        try:
            # Общее количество
            total_query = select(func.count()).select_from(self.model)
            total_result = await session.execute(total_query)
            total = total_result.scalar() or 0
            
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
            
            statistics = {
                "total_asteroids": total,
                "pha_count": pha_count,
                "percent_pha": round((pha_count / total * 100) if total > 0 else 0, 1),
                "average_diameter_km": avg_diameter,
                "min_moid_au": min_moid,
                "last_updated": datetime.now().isoformat()
            }
            
            logger.debug(f"Статистика астероидов: {statistics}")
            return statistics
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики астероидов: {e}")
            raise