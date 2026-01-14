"""
Контроллер для работы с оценками угроз из NASA Sentry API.
Использует общие методы BaseController.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
import logging

from models.threat_assessment import ThreatAssessmentModel
from .base_controller import BaseController

logger = logging.getLogger(__name__)


class ThreatController(BaseController[ThreatAssessmentModel]):
    """Контроллер для операций с оценками угроз (One-to-One)."""
    
    def __init__(self):
        """Инициализирует контроллер для модели ThreatAssessmentModel."""
        super().__init__(ThreatAssessmentModel)
        logger.info("Инициализирован ThreatController (One-to-One)")
    
    async def get_by_designation(self, session: AsyncSession, designation: str) -> Optional[ThreatAssessmentModel]:
        """
        Получает оценку угрозы по обозначению астероида.
        Без коммита (чтение).
        """
        return await self._find_by_fields(session, {"designation": designation})
    
    async def get_by_asteroid_id(
        self, 
        session: AsyncSession, 
        asteroid_id: int
    ) -> Optional[ThreatAssessmentModel]:
        """
        Получает оценку угрозы для конкретного астероида (One-to-One).
        Без коммита (чтение).
        """
        return await self._find_by_fields(session, {"asteroid_id": asteroid_id})
    
    async def get_high_risk_threats(
        self, 
        session: AsyncSession, 
        limit: int = 20
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы с высоким уровнем риска (ts_max >= 5).
        Без коммита (чтение).
        """
        return await self.filter(
            session=session,
            filters={"ts_max__ge": 5},
            limit=limit,
            order_by="ts_max",
            order_desc=True
        )
    
    async def get_threats_by_risk_level(
        self,
        session: AsyncSession,
        min_ts: int = 0,
        max_ts: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы по диапазону значений Туринской шкалы.
        Без коммита (чтение).
        """
        filters = {
            "ts_max__ge": min_ts,
            "ts_max__le": max_ts
        }
        
        return await self.filter(
            session=session,
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="ts_max",
            order_desc=True
        )
    
    async def get_threats_by_probability(
        self,
        session: AsyncSession,
        min_probability: float = 0.0,
        max_probability: float = 1.0,
        skip: int = 0,
        limit: int = 100
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы по диапазону вероятности столкновения.
        Без коммита (чтение).
        """
        filters = {
            "ip__ge": min_probability,
            "ip__le": max_probability
        }
        
        return await self.filter(
            session=session,
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="ip",
            order_desc=True
        )
    
    async def get_threats_by_energy(
        self,
        session: AsyncSession,
        min_energy: float = 0.0,
        max_energy: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы по диапазону энергии воздействия.
        Без коммита (чтение).
        """
        filters = {"energy_megatons__ge": min_energy}
        
        if max_energy is not None:
            filters["energy_megatons__le"] = max_energy
        
        return await self.filter(
            session=session,
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="energy_megatons",
            order_desc=True
        )
    
    async def get_threats_by_impact_category(
        self,
        session: AsyncSession,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы по категории воздействия.
        Без коммита (чтение).
        """
        return await self.filter(
            session=session,
            filters={"impact_category": category},
            skip=skip,
            limit=limit,
            order_by="energy_megatons",
            order_desc=True
        )
    
    async def update_threat_assessment(
        self,
        session: AsyncSession,
        designation: str,
        new_data: Dict[str, Any]
    ) -> Optional[ThreatAssessmentModel]:
        """
        Обновляет оценку угрозы для астероида с коммитом.
        """
        threat = await self.get_by_designation(session, designation)
        
        if not threat:
            logger.warning(f"Попытка обновления несуществующей оценки угрозы для {designation}")
            return None
        
        threat = await self.update(session, threat.id, new_data)
        
        return threat
    
    async def bulk_create_threats(
        self,
        session: AsyncSession,
        threats_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое создание оценок угроз (One-to-One) с коммитом.
        """
        created, updated = await self.bulk_create(
            session=session,
            data_list=threats_data,
            conflict_action="update",
            conflict_fields=["asteroid_id"]  # Уникальное поле для One-to-One
        )
        
        return created, updated
    
    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает статистику по оценкам угроз.
        Без коммита (чтение).
        """
        try:
            # Общее количество
            total = await self.count(session)
            
            # Распределение по уровням Туринской шкалы
            ts_stats = {}
            for ts in range(0, 11):
                ts_query = select(func.count()).where(self.model.ts_max == ts)
                ts_result = await session.execute(ts_query)
                count = ts_result.scalar() or 0
                ts_stats[f"ts_{ts}"] = {
                    'count': count,
                    'percent': round((count / total * 100) if total > 0 else 0, 1)
                }
            
            # Распределение по категориям воздействия
            category_stats = {}
            for category in ['локальный', 'региональный', 'глобальный']:
                cat_query = select(func.count()).where(self.model.impact_category == category)
                cat_result = await session.execute(cat_query)
                count = cat_result.scalar() or 0
                category_stats[category] = {
                    'count': count,
                    'percent': round((count / total * 100) if total > 0 else 0, 1)
                }
            
            # Средняя вероятность
            avg_prob_query = select(func.avg(self.model.ip))
            avg_prob_result = await session.execute(avg_prob_query)
            avg_probability = avg_prob_result.scalar() or 0
            
            # Максимальная энергия
            max_energy_query = select(func.max(self.model.energy_megatons))
            max_energy_result = await session.execute(max_energy_query)
            max_energy = max_energy_result.scalar() or 0
            
            # Средняя энергия
            avg_energy_query = select(func.avg(self.model.energy_megatons))
            avg_energy_result = await session.execute(avg_energy_query)
            avg_energy = round(avg_energy_result.scalar() or 0, 1)
            
            # Количество угроз с ненулевой вероятностью
            non_zero_query = select(func.count()).where(self.model.ip > 0)
            non_zero_result = await session.execute(non_zero_query)
            non_zero_count = non_zero_result.scalar() or 0
            
            # Количество угроз с высоким риском (ts_max >= 5)
            high_risk_query = select(func.count()).where(self.model.ts_max >= 5)
            high_risk_result = await session.execute(high_risk_query)
            high_risk_count = high_risk_result.scalar() or 0
            
            return {
                "total_threats": total,
                "torino_scale_distribution": ts_stats,
                "impact_category_distribution": category_stats,
                "average_probability": avg_probability,
                "average_energy_mt": avg_energy,
                "max_energy_mt": max_energy,
                "non_zero_probability_count": non_zero_count,
                "high_risk_count": high_risk_count,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики оценок угроз: {e}")
            raise
    
    async def search_threats(
        self,
        session: AsyncSession,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ThreatAssessmentModel]:
        """
        Ищет угрозы по обозначению или полному названию астероида.
        Без коммита (чтение).
        """
        return await self.search(
            session=session,
            search_term=search_term,
            search_fields=["designation", "fullname"],
            skip=skip,
            limit=limit
        )