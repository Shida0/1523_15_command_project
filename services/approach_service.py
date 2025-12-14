"""
Сервис для работы со сближениями астероидов с Землей.
Содержит методы для поиска, фильтрации и анализа сближений.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from controllers.approach_controller import ApproachController
from controllers.asteroid_controller import AsteroidController
from .base_service import ServiceWithController

logger = logging.getLogger(__name__)


class ApproachService(ServiceWithController[ApproachController]):
    """Сервис для операций со сближениями."""
    
    def __init__(self):
        """Инициализирует сервис с контроллерами."""
        super().__init__(ApproachController())
        self.asteroid_controller = AsteroidController()
        logger.info("Инициализирован ApproachService")
    
    async def get_upcoming_approaches(
        self, 
        session: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Получает сближения на ближайшие N дней.
        
        Args:
            session: Сессия БД
            days: Количество дней для поиска вперед
            
        Returns:
            Список сближений с данными об астероидах
        """
        self.log_service_call("get_upcoming_approaches", days=days)
        
        try:
            # Определяем временной диапазон
            now = datetime.now()
            start_date = now
            end_date = now + timedelta(days=days)
            
            # Получаем сближения в этом диапазоне
            approaches = await self.controller.get_approaches_in_period(
                session, 
                start_date, 
                end_date
            )
            
            # Добавляем информацию об астероидах
            result = []
            for approach in approaches:
                asteroid = await self.asteroid_controller.get_by_id(session, approach.asteroid_id)
                
                if asteroid:
                    result.append({
                        "approach": self.model_to_dict(approach),
                        "asteroid": self.model_to_dict(asteroid)
                    })
            
            # Сортируем по дате сближения
            result.sort(key=lambda x: x["approach"]["approach_time"])
            
            self.log_service_result("get_upcoming_approaches", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_upcoming_approaches", e, session)
            return []
    
    async def get_closest_approaches_by_distance(
        self, 
        session: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Ищет самые близкие сближения по расстоянию.
        
        Args:
            session: Сессия БД
            limit: Количество ближайших сближений
            
        Returns:
            Список ближайших сближений с данными об астероидах
        """
        self.log_service_call("get_closest_approaches_by_distance", limit=limit)
        
        try:
            # Получаем самые близкие сближения
            approaches = await self.controller.get_closest_by_distance(session, limit)
            
            # Добавляем информацию об астероидах
            result = []
            for approach in approaches:
                asteroid = await self.asteroid_controller.get_by_id(session, approach.asteroid_id)
                
                if asteroid:
                    result.append({
                        "approach": self.model_to_dict(approach),
                        "asteroid": self.model_to_dict(asteroid)
                    })
            
            self.log_service_result("get_closest_approaches_by_distance", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_closest_approaches_by_distance", e, session)
            return []
    
    async def find_approaches_for_asteroid(
        self, 
        session: AsyncSession,
        asteroid_id: int
    ) -> List[Dict[str, Any]]:
        """
        Находит все сближения конкретного астероида.
        
        Args:
            session: Сессия БД
            asteroid_id: ID астероида
            
        Returns:
            Список сближений астероида, отсортированных по дате
        """
        self.log_service_call("find_approaches_for_asteroid", asteroid_id=asteroid_id)
        
        try:
            # Получаем все сближения астероида
            approaches = await self.controller.get_by_asteroid(session, asteroid_id)
            
            # Преобразуем в словари
            result = [self.model_to_dict(approach) for approach in approaches]
            
            # Уже отсортированы в контроллере
            self.log_service_result("find_approaches_for_asteroid", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("find_approaches_for_asteroid", e, session)
            return []
    
    async def get_approaches_in_date_range(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        max_distance_au: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает сближения в указанном временном диапазоне.
        
        Args:
            session: Сессия БД
            start_date: Начальная дата
            end_date: Конечная дата
            max_distance_au: Максимальное расстояние в а.е.
            
        Returns:
            Список сближений в диапазоне
        """
        self.log_service_call(
            "get_approaches_in_date_range", 
            start_date=start_date, 
            end_date=end_date, 
            max_distance_au=max_distance_au
        )
        
        try:
            approaches = await self.controller.get_approaches_in_period(
                session, 
                start_date, 
                end_date, 
                max_distance_au
            )
            
            result = [self.model_to_dict(approach) for approach in approaches]
            
            self.log_service_result("get_approaches_in_date_range", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_approaches_in_date_range", e, session)
            return []
    
    async def get_closest_approaches_by_time(
        self,
        session: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получает ближайшие по времени сближения.
        
        Args:
            session: Сессия БД
            limit: Количество ближайших сближений
            
        Returns:
            Список ближайших сближений
        """
        self.log_service_call("get_closest_approaches_by_time", limit=limit)
        
        try:
            approaches = await self.controller.get_closest_approaches(session, limit)
            
            # Добавляем информацию об астероидах
            result = []
            for approach in approaches:
                asteroid = await self.asteroid_controller.get_by_id(session, approach.asteroid_id)
                
                if asteroid:
                    result.append({
                        "approach": self.model_to_dict(approach),
                        "asteroid": self.model_to_dict(asteroid)
                    })
            
            self.log_service_result("get_closest_approaches_by_time", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_closest_approaches_by_time", e, session)
            return []