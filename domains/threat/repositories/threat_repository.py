# -*- coding: utf-8 -*-
"""
Репозиторий для работы с оценками угроз из NASA Sentry API.
Использует общие методы BaseController.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
import logging

from domains.threat.models.threat_assessment import ThreatAssessmentModel
from shared.infrastructure import BaseRepository

logger = logging.getLogger(__name__)

class ThreatRepository(BaseRepository[ThreatAssessmentModel]):
    """Репозиторий для операций с оценками угроз (One-to-One)."""
    
    def __init__(self):
        """Инициализирует репозиторий для модели ThreatAssessmentModel."""
        super().__init__(ThreatAssessmentModel)
        logger.info("Инициализирован ThreatRepository (One-to-One)")
    
    async def get_by_designation(self, designation: str) -> Optional[ThreatAssessmentModel]:
        """
        Получает оценку угрозы по обозначению астероида.
        Без коммита (чтение).
        """
        return await self._find_by_fields({"designation": designation})
    
    async def get_by_asteroid_id(
        self,
        asteroid_id: int
    ) -> Optional[ThreatAssessmentModel]:
        """
        Получает оценку угрозы для конкретного астероида (One-to-One).
        Без коммита (чтение).
        """
        return await self._find_by_fields({"asteroid_id": asteroid_id})
    
    async def get_high_risk_threats(
        self,
        limit: int = 20,
        skip: int = 0
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы с высоким уровнем риска (ts_max >= 5).
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"ts_max__ge": 5},
            skip=skip,
            limit=limit,
            order_by="ts_max",
            order_desc=True
        )
    
    async def get_threats_by_risk_level(
        self,
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
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="ts_max",
            order_desc=True
        )
    
    async def get_threats_by_probability(
        self,
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
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="ip",
            order_desc=True
        )
    
    async def get_threats_by_energy(
        self,
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
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="energy_megatons",
            order_desc=True
        )
    
    async def get_threats_by_impact_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ThreatAssessmentModel]:
        """
        Получает угрозы по категории воздействия.
        Без коммита (чтение).
        """
        return await self.filter(
            filters={"impact_category": category},
            skip=skip,
            limit=limit,
            order_by="energy_megatons",
            order_desc=True
        )
    
    async def update_threat_assessment(
        self,
        designation: str,
        new_data: Dict[str, Any]
    ) -> Optional[ThreatAssessmentModel]:
        """
        Обновляет оценку угрозы для астероида с коммитом.
        """
        threat = await self.get_by_designation(designation)

        if not threat:
            logger.warning(f"Попытка обновления несуществующей оценки угрозы для {designation}")
            return None

        threat = await self.update(threat.id, new_data)

        return threat
    
    async def bulk_create_threats(
        self,
        threats_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое создание оценок угроз (One-to-One) с коммитом.
        """
        created, updated = await self.bulk_create(
            data_list=threats_data,
            conflict_action="update",
            conflict_fields=["asteroid_id"]  # Уникальное поле для One-to-One
        )

        return created, updated
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по оценкам угроз.
        Без коммита (чтение).
        """
        try:
            # Общее количество
            total = await self.count()

            # Распределение по уровням Туринской шкалы
            ts_stats = {}
            for ts in range(0, 11):
                ts_query = select(func.count()).where(self.model.ts_max == ts)
                ts_result = await self.session.execute(ts_query)
                ts_scalar = ts_result.scalar()
                # Handle the case where scalar returns a coroutine due to mocking in tests
                if hasattr(ts_scalar, '__await__'):
                    count = await ts_scalar
                else:
                    count = ts_scalar
                count_val = count or 0
                percent = round((count_val / total * 100) if total > 0 else 0, 1)
                ts_stats[f"ts_{ts}"] = {
                    'count': count_val,
                    'percent': percent
                }

            # Распределение по категориям воздействия
            category_stats = {}
            for category in ['локальный', 'региональный', 'глобальный']:
                cat_query = select(func.count()).where(self.model.impact_category == category)
                cat_result = await self.session.execute(cat_query)
                cat_scalar = cat_result.scalar()
                # Handle the case where scalar returns a coroutine due to mocking in tests
                if hasattr(cat_scalar, '__await__'):
                    count = await cat_scalar
                else:
                    count = cat_scalar
                count_val = count or 0
                percent = round((count_val / total * 100) if total > 0 else 0, 1)
                category_stats[category] = {
                    'count': count_val,
                    'percent': percent
                }

            # Средняя вероятность
            avg_prob_query = select(func.avg(self.model.ip))
            avg_prob_result = await self.session.execute(avg_prob_query)
            avg_prob_scalar = avg_prob_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(avg_prob_scalar, '__await__'):
                avg_prob_value = await avg_prob_scalar
            else:
                avg_prob_value = avg_prob_scalar
            
            # Handle None value when there are no records
            if avg_prob_value is None:
                avg_probability = 0.0
            else:
                avg_probability = round(avg_prob_value, 6)

            # Максимальная энергия
            max_energy_query = select(func.max(self.model.energy_megatons))
            max_energy_result = await self.session.execute(max_energy_query)
            max_energy_scalar = max_energy_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(max_energy_scalar, '__await__'):
                max_energy_value = await max_energy_scalar
            else:
                max_energy_value = max_energy_scalar
            
            # Handle None value when there are no records
            if max_energy_value is None:
                max_energy = 0.0
            else:
                max_energy = float(max_energy_value)

            # Средняя энергия
            avg_energy_query = select(func.avg(self.model.energy_megatons))
            avg_energy_result = await self.session.execute(avg_energy_query)
            avg_energy_scalar = avg_energy_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(avg_energy_scalar, '__await__'):
                avg_energy_value = await avg_energy_scalar
            else:
                avg_energy_value = avg_energy_scalar
            
            # Handle None value when there are no records
            if avg_energy_value is None:
                avg_energy = 0.0
            else:
                avg_energy = round(avg_energy_value, 1)

            # Количество угроз с ненулевой вероятностью
            non_zero_query = select(func.count()).where(self.model.ip > 0)
            non_zero_result = await self.session.execute(non_zero_query)
            non_zero_scalar = non_zero_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(non_zero_scalar, '__await__'):
                non_zero_value = await non_zero_scalar
            else:
                non_zero_value = non_zero_scalar
            non_zero_count = non_zero_value or 0

            # Количество угроз с высоким риском (ts_max >= 5)
            high_risk_query = select(func.count()).where(self.model.ts_max >= 5)
            high_risk_result = await self.session.execute(high_risk_query)
            high_risk_scalar = high_risk_result.scalar()
            # Handle the case where scalar returns a coroutine due to mocking in tests
            if hasattr(high_risk_scalar, '__await__'):
                high_risk_value = await high_risk_scalar
            else:
                high_risk_value = high_risk_scalar
            high_risk_count = high_risk_value or 0

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
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ThreatAssessmentModel]:
        """
        Ищет угрозы по обозначению или полному названию астероида.
        Без коммита (чтение).
        """
        return await self.search(
            search_term=search_term,
            search_fields=["designation", "fullname"],
            skip=skip,
            limit=limit
        )
