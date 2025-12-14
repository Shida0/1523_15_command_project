"""
Сервис для оценки опасности сближений.
Содержит методы расчета рисков и анализа угроз.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import math
import logging

from controllers.threat_controller import ThreatController
from controllers.approach_controller import ApproachController
from controllers.asteroid_controller import AsteroidController
from .base_service import ServiceWithController

logger = logging.getLogger(__name__)


class ThreatAssessmentService(ServiceWithController[ThreatController]):
    """Сервис для операций с оценками угроз."""
    
    def __init__(self):
        """Инициализирует сервис с контроллерами."""
        super().__init__(ThreatController())
        self.approach_controller = ApproachController()
        self.asteroid_controller = AsteroidController()
        logger.info("Инициализирован ThreatAssessmentService")
    
    def calculate_approach_risk(
        self, 
        approach_data: Dict[str, Any], 
        asteroid_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Оценивает риск для одного сближения.
        
        Args:
            approach_data: Данные сближения (расстояние, скорость, время)
            asteroid_data: Данные астероида (диаметр, MOID)
            
        Returns:
            Словарь с оценкой риска
        """
        self.log_service_call("calculate_approach_risk", 
                            approach_data_keys=list(approach_data.keys()),
                            asteroid_data_keys=list(asteroid_data.keys()))
        
        try:
            # Извлекаем данные
            distance_au = approach_data.get('distance_au', 1.0)
            velocity_km_s = approach_data.get('velocity_km_s', 20.0)
            
            diameter_km = asteroid_data.get('estimated_diameter_km', 0.1)
            asteroid_moid = asteroid_data.get('earth_moid_au', 0.1)
            
            # Определяем уровень угрозы по расстоянию
            if distance_au < 0.02:
                threat_level = "критический"
            elif distance_au < 0.05:
                threat_level = "высокий"
            elif distance_au < 0.1:
                threat_level = "средний"
            else:
                threat_level = "низкий"
            
            # Рассчитываем энергию
            energy_megatons = self._calculate_kinetic_energy(diameter_km, velocity_km_s)
            
            # Определяем тип воздействия
            impact_type = self._determine_impact_type(energy_megatons, diameter_km)
            
            result = {
                "threat_level": threat_level,
                "energy_megatons": round(energy_megatons, 2),
                "impact_type": impact_type,
                "distance_au": distance_au,
                "diameter_km": diameter_km,
                "velocity_km_s": velocity_km_s
            }
            
            self.log_service_result("calculate_approach_risk", result)
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка расчета риска: {e}")
            return {
                "threat_level": "неизвестно",
                "energy_megatons": 0.0,
                "impact_type": "неизвестно",
                "error": str(e)
            }
    
    def _calculate_kinetic_energy(self, diameter_km: float, velocity_km_s: float) -> float:
        """
        Рассчитывает кинетическую энергию в мегатоннах тротила.
        
        Args:
            diameter_km: Диаметр астероида в км
            velocity_km_s: Скорость в км/с
            
        Returns:
            Энергия в мегатоннах
        """
        # Плотность каменного астероида (кг/м³)
        density = 2000.0
        
        # Преобразуем диаметр в метры и считаем объем сферы
        diameter_m = diameter_km * 1000
        radius_m = diameter_m / 2
        volume_m3 = (4/3) * math.pi * (radius_m ** 3)
        
        # Масса
        mass_kg = density * volume_m3
        
        # Скорость в м/с
        velocity_m_s = velocity_km_s * 1000
        
        # Кинетическая энергия в джоулях
        energy_joules = 0.5 * mass_kg * (velocity_m_s ** 2)
        
        # Конвертация в мегатонны тротила (1 Мт = 4.184e15 Дж)
        energy_megatons = energy_joules / 4.184e15
        
        return energy_megatons
    
    def _determine_impact_type(self, energy_megatons: float, diameter_km: float) -> str:
        """
        Определяет тип воздействия на основе энергии и диаметра.
        
        Args:
            energy_megatons: Энергия в мегатоннах
            diameter_km: Диаметр в км
            
        Returns:
            Тип воздействия
        """
        if energy_megatons < 1:
            return "локальный (атмосферный взрыв)"
        elif energy_megatons < 10:
            return "локальный (небольшой кратер)"
        elif energy_megatons < 100:
            return "региональный (разрушения в радиусе 100 км)"
        elif energy_megatons < 1000:
            return "региональный (катастрофа регионального масштаба)"
        else:
            return "глобальный (катастрофа глобального масштаба)"
    
    async def get_high_risk_approaches(
        self, 
        session: AsyncSession,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Ищет сближения с высоким уровнем риска.
        
        Args:
            session: Сессия БД
            limit: Максимальное количество записей
            
        Returns:
            Список опасных сближений с данными об астероидах
        """
        self.log_service_call("get_high_risk_approaches", limit=limit)
        
        try:
            # Получаем оценки с высоким уровнем угрозы
            threats = await self.controller.get_high_threats(session, limit)
            
            result = []
            for threat in threats:
                # Получаем сближение
                approach = await self.approach_controller.get_by_id(session, threat.approach_id)
                
                if approach:
                    # Получаем астероид
                    asteroid = await self.asteroid_controller.get_by_id(session, approach.asteroid_id)
                    
                    if asteroid:
                        result.append({
                            "threat": self.model_to_dict(threat),
                            "approach": self.model_to_dict(approach),
                            "asteroid": self.model_to_dict(asteroid)
                        })
            
            self.log_service_result("get_high_risk_approaches", result)
            return result
            
        except Exception as e:
            await self.handle_service_error("get_high_risk_approaches", e, session)
            return []
    
    async def get_threat_statistics(
        self, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Получает статистику по оценкам угроз.
        
        Args:
            session: Сессия БД
            
        Returns:
            Словарь со статистикой
        """
        self.log_service_call("get_threat_statistics")
        
        try:
            stats = await self.controller.get_statistics(session)
            self.log_service_result("get_threat_statistics", stats)
            return stats
            
        except Exception as e:
            await self.handle_service_error("get_threat_statistics", e, session)
            return {}
    
    async def assess_approach(
        self,
        session: AsyncSession,
        approach_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Оценивает риск для конкретного сближения.
        
        Args:
            session: Сессия БД
            approach_id: ID сближения
            
        Returns:
            Оценка риска или None
        """
        self.log_service_call("assess_approach", approach_id=approach_id)
        
        try:
            # Получаем сближение
            approach = await self.approach_controller.get_by_id(session, approach_id)
            
            if not approach:
                self.logger.warning(f"Сближение с ID {approach_id} не найдено")
                return None
            
            # Получаем астероид
            asteroid = await self.asteroid_controller.get_by_id(session, approach.asteroid_id)
            
            if not asteroid:
                self.logger.warning(f"Астероид для сближения {approach_id} не найден")
                return None
            
            # Преобразуем в словари
            approach_dict = self.model_to_dict(approach)
            asteroid_dict = self.model_to_dict(asteroid)
            
            # Рассчитываем риск
            risk_assessment = self.calculate_approach_risk(approach_dict, asteroid_dict)
            
            # Проверяем, есть ли уже оценка в БД
            existing_threat = await self.controller.get_by_approach_id(session, approach_id)
            
            if existing_threat:
                risk_assessment["db_id"] = existing_threat.id
                risk_assessment["exists_in_db"] = True
            else:
                risk_assessment["exists_in_db"] = False
            
            self.log_service_result("assess_approach", risk_assessment)
            return risk_assessment
            
        except Exception as e:
            await self.handle_service_error("assess_approach", e, session)
            return None