from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import logging

from domains.asteroid import AsteroidModel
from shared.infrastructure import BaseRepository

logger = logging.getLogger(__name__)


class AsteroidRepository(BaseRepository[AsteroidModel]):
    """Репозиторий для операций с астероидами"""

    def __init__(self):
        """Инициализирует репозиторий для модели AsteroidModel"""
        super().__init__(AsteroidModel)
        logger.info("Инициализирован AsteroidRepository")

    async def get_by_designation(self, designation: str) -> Optional[AsteroidModel]:
        """Находит астероид по обозначению NASA"""
        return await self._find_by_fields({"designation": designation})

    async def get_asteroids_by_earth_moid(self, max_moid: float, skip: int = 0, limit: Optional[int] = None) -> List[AsteroidModel]:
        """Получает астероиды с MOID меньше указанного значения"""
        return await self.filter({"earth_moid_au__le": max_moid}, skip, limit, order_by="earth_moid_au")

    async def get_all(self, skip: int = 0, limit: Optional[int] = None) -> List[AsteroidModel]:
        """Получает все астероиды с поддержкой пагинации"""
        return await self.filter({}, skip, limit, order_by="designation")

    async def get_asteroids_count(self, max_moid: float = 1.0) -> int:
        """Получает общее количество астероидов с MOID меньше указанного значения"""
        try:
            query = select(func.count()).where(self.model.earth_moid_au <= max_moid)
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Ошибка получения количества астероидов: {e}")
            return 0

    async def get_asteroids_with_accurate_diameter(self, skip: int = 0, limit: Optional[int] = None) -> List[AsteroidModel]:
        """Получает астероиды с точными данными о диаметре"""
        return await self.filter({"accurate_diameter": True}, skip, limit, order_by="estimated_diameter_km")

    async def get_asteroids_by_orbit_class(self, orbit_class: str, skip: int = 0, limit: Optional[int] = None) -> List[AsteroidModel]:
        """Получает астероиды по классу орбиты"""
        return await self.filter({"orbit_class": orbit_class}, skip, limit, order_by="designation")

    async def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по астероидам"""
        try:
            total = await self.count()

            avg_diameter_query = select(func.avg(self.model.estimated_diameter_km))
            avg_diameter_result = await self.session.execute(avg_diameter_query)
            avg_diameter_scalar = avg_diameter_result.scalar()
            if hasattr(avg_diameter_scalar, '__await__'):
                avg_diameter_value = await avg_diameter_scalar
            else:
                avg_diameter_value = avg_diameter_scalar
            avg_diameter = round(avg_diameter_value or 0, 2)

            min_moid_query = select(func.min(self.model.earth_moid_au))
            min_moid_result = await self.session.execute(min_moid_query)
            min_moid_scalar = min_moid_result.scalar()
            if hasattr(min_moid_scalar, '__await__'):
                min_moid_value = await min_moid_scalar
            else:
                min_moid_value = min_moid_scalar
            min_moid = min_moid_value or 0

            accurate_count_query = select(func.count()).where(self.model.accurate_diameter == True)
            accurate_count_result = await self.session.execute(accurate_count_query)
            accurate_count_scalar = accurate_count_result.scalar()
            if hasattr(accurate_count_scalar, '__await__'):
                accurate_count_value = await accurate_count_scalar
            else:
                accurate_count_value = accurate_count_scalar
            accurate_count = accurate_count_value or 0

            source_stats = {}
            for source in ['measured', 'computed', 'calculated']:
                source_query = select(func.count()).where(self.model.diameter_source == source)
                source_result = await self.session.execute(source_query)
                source_scalar = source_result.scalar()
                if hasattr(source_scalar, '__await__'):
                    source_value = await source_scalar
                else:
                    source_value = source_scalar
                source_stats[source] = source_value or 0

            return {
                "total_asteroids": total,
                "average_diameter_km": avg_diameter,
                "min_earth_moid_au": min_moid,
                "accurate_diameter_count": accurate_count,
                "percent_accurate": round((accurate_count / total * 100) if total > 0 else 0, 1),
                "diameter_source_stats": source_stats,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики астероидов: {e}")
            raise

    async def bulk_create_asteroids(self, asteroids_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Массовое создание астероидов"""
        created, updated = await self.bulk_create(asteroids_data, "update", ["designation"])
        return created, updated

    async def delete_asteroids_not_in_designations(self, designations: List[str]) -> int:
        """Удаляет астероиды, которых нет в списке designations"""
        try:
            from sqlalchemy import delete
            query = delete(self.model).where(self.model.designation.notin_(designations))
            result = await self.session.execute(query)
            await self.session.commit()
            deleted_count = result.rowcount
            logger.info(f"Удалено {deleted_count} астероидов, которых нет в списке NASA")
            return deleted_count
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка удаления астероидов: {e}")
            return 0
