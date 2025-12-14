"""
Сервис для работы с астероидами.
Содержит бизнес-логику для обработки и анализа данных об астероидах.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from controllers.asteroid_controller import AsteroidController
from controllers.approach_controller import ApproachController
from controllers.threat_controller import ThreatController
from .base_service import ServiceWithController

logger = logging.getLogger(__name__)


class AsteroidService(ServiceWithController[AsteroidController]):
    """Сервис для операций с астероидами."""
    
    def __init__(self):
        """Инициализирует сервис с контроллерами."""
        super().__init__(AsteroidController())
        self.approach_controller = ApproachController()
        self.threat_controller = ThreatController()
        logger.info("Инициализирован AsteroidService")
    
    async def get_asteroid_details(
        self, 
        session: AsyncSession, 
        asteroid_id: int
    ) -> Dict[str, Any]:
        """
        Получает полную информацию об астероиде.
        
        Args:
            session: Сессия БД
            asteroid_id: ID астероида
            
        Returns:
            Словарь с данными астероида, сближениями и оценками рисков
        """
        self.log_service_call("get_asteroid_details", asteroid_id=asteroid_id)
        
        try:
            # Получаем базовую информацию об астероиде
            asteroid = await self.controller.get_by_id(session, asteroid_id)
            
            if not asteroid:
                self.logger.warning(f"Астероид с ID {asteroid_id} не найден")
                return {}
            
            # Получаем все сближения астероида
            approaches = await self.approach_controller.get_by_asteroid(session, asteroid_id)
            
            # Для каждого сближения получаем оценку риска
            approaches_with_risk = []
            for approach in approaches:
                threat_assessment = await self.threat_controller.get_by_approach_id(
                    session, 
                    approach.id
                )
                
                approaches_with_risk.append({
                    "approach": self.model_to_dict(approach),
                    "risk": self.model_to_dict(threat_assessment) if threat_assessment else None
                })
            
            # Формируем результат
            result = {
                "asteroid": self.model_to_dict(asteroid),
                "approaches": approaches_with_risk,
                "approaches_count": len(approaches_with_risk)
            }
            
            self.log_service_result("get_asteroid_details", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_asteroid_details", e, session)
            return {}
    
    async def calculate_asteroid_risk_score(
        self, 
        session: AsyncSession, 
        asteroid_id: int
    ) -> float:
        """
        Рассчитывает простой показатель опасности астероида.
        
        Формула: Риск = (размер_в_км / 10) * (1 / MOID_ае) * (количество_близких_сближений / 10)
        
        Args:
            session: Сессия БД
            asteroid_id: ID астероида
            
        Returns:
            Число от 0 до 100
        """
        self.log_service_call("calculate_asteroid_risk_score", asteroid_id=asteroid_id)
        
        try:
            # Получаем данные астероида
            asteroid = await self.controller.get_by_id(session, asteroid_id)
            
            if not asteroid:
                self.logger.warning(f"Астероид с ID {asteroid_id} не найден")
                return 0.0
            
            # Получаем все сближения астероида
            approaches = await self.approach_controller.get_by_asteroid(session, asteroid_id)
            
            # Считаем количество близких сближений (< 0.1 а.е.)
            close_approaches = 0
            for approach in approaches:
                if approach.distance_au < 0.1:
                    close_approaches += 1
            
            # Извлекаем параметры для расчета
            diameter_km = asteroid.estimated_diameter_km
            moid_au = asteroid.earth_moid_au
            
            # Защита от деления на ноль и недопустимых значений
            if moid_au <= 0:
                moid_au = 0.0001  # Минимальное значение
                
            if diameter_km <= 0:
                diameter_km = 0.0001
            
            # Расчет по упрощенной формуле
            size_factor = diameter_km / 10.0
            moid_factor = 1.0 / moid_au
            frequency_factor = close_approaches / 10.0
            
            risk_score = size_factor * moid_factor * frequency_factor
            
            # Ограничиваем значение от 0 до 100
            risk_score = max(0.0, min(risk_score, 100.0))
            
            self.logger.debug(
                f"Расчет риска для астероида {asteroid_id}: "
                f"диаметр={diameter_km:.2f}км, MOID={moid_au:.4f}а.е., "
                f"близких_сближений={close_approaches}, риск={risk_score:.2f}"
            )
            
            return round(risk_score, 2)
            
        except Exception as e:
            await self.handle_service_error("calculate_asteroid_risk_score", e, session)
            return 0.0
    
    async def filter_asteroids_simple(
        self, 
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Фильтрует астероиды по простым параметрам.
        
        Args:
            session: Сессия БД
            filters: Словарь с фильтрами
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список отфильтрованных астероидов
        """
        self.log_service_call("filter_asteroids_simple", filters=filters, skip=skip, limit=limit)
        
        try:
            # Базовый запрос
            asteroids = await self.controller.get_all(session, skip, limit)
            
            # Применяем фильтры
            filtered_asteroids = []
            
            for asteroid in asteroids:
                include = True
                
                # Фильтр по диаметру
                min_diameter = filters.get('min_diameter')
                if min_diameter is not None:
                    if asteroid.estimated_diameter_km < min_diameter:
                        include = False
                
                # Фильтр по MOID
                max_moid = filters.get('moid_less_than')
                if max_moid is not None:
                    if asteroid.earth_moid_au > max_moid:
                        include = False
                
                # Фильтр по PHA
                is_pha = filters.get('is_pha')
                if is_pha is not None:
                    if asteroid.is_pha != is_pha:
                        include = False
                
                # Фильтр по NEO
                is_neo = filters.get('is_neo')
                if is_neo is not None:
                    if asteroid.is_neo != is_neo:
                        include = False
                
                if include:
                    filtered_asteroids.append(self.model_to_dict(asteroid))
            
            self.log_service_result("filter_asteroids_simple", filtered_asteroids)
            return filtered_asteroids
            
        except Exception as e:
            await self.handle_service_error("filter_asteroids_simple", e, session)
            return []
    
    async def get_asteroid_by_mpc(
        self, 
        session: AsyncSession, 
        mpc_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получает астероид по номеру MPC.
        
        Args:
            session: Сессия БД
            mpc_number: Номер MPC
            
        Returns:
            Данные астероида или None
        """
        self.log_service_call("get_asteroid_by_mpc", mpc_number=mpc_number)
        
        try:
            asteroid = await self.controller.get_by_mpc_number(session, mpc_number)
            
            if asteroid:
                result = self.model_to_dict(asteroid)
                self.log_service_result("get_asteroid_by_mpc", result)
                return result
            else:
                self.logger.debug(f"Астероид с MPC номером {mpc_number} не найден")
                return None
                
        except Exception as e:
            await self.handle_service_error("get_asteroid_by_mpc", e, session)
            return None
    
    async def get_pha_asteroids(
        self, 
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получает только потенциально опасные астероиды.
        
        Args:
            session: Сессия БД
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список PHA астероидов
        """
        self.log_service_call("get_pha_asteroids", skip=skip, limit=limit)
        
        try:
            asteroids = await self.controller.get_pha_asteroids(session, skip, limit)
            result = [self.model_to_dict(asteroid) for asteroid in asteroids]
            
            self.log_service_result("get_pha_asteroids", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_pha_asteroids", e, session)
            return []
    
    async def get_asteroid_statistics(
        self, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Получает базовую статистику по астероидам.
        
        Args:
            session: Сессия БД
            
        Returns:
            Словарь со статистикой
        """
        self.log_service_call("get_asteroid_statistics")
        
        try:
            # Используем метод контроллера для получения статистики
            stats = await self.controller.get_statistics(session)
            
            # Добавляем временную метку
            stats["calculated_at"] = datetime.now().isoformat()
            
            self.log_service_result("get_asteroid_statistics", stats)
            return stats
            
        except Exception as e:
            await self.handle_service_error("get_asteroid_statistics", e, session)
            return {}