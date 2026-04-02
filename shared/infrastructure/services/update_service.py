import logging
from datetime import datetime
from typing import Optional

from domains.asteroid import AsteroidService
from domains.approach import ApproachService
from domains.threat import ThreatService
from shared.external_api.wrappers.get_data import get_asteroid_data
from shared.external_api.wrappers.get_approaches import get_current_close_approaches
from shared.external_api.wrappers.get_threat import get_all_threats
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class UpdateService:
    """Сервис для периодического обновления данных из NASA API"""

    def __init__(self, session_factory):
        """Инициализация сервиса обновления"""
        self.session_factory = session_factory

        self.asteroid_service = AsteroidService(session_factory)
        self.approach_service = ApproachService(session_factory)
        self.threat_service = ThreatService(session_factory)

        logger.info("UpdateService инициализирован")

    async def update_asteroids(self, limit: Optional[int] = None) -> int:
        """Обновление астероидов с надёжной обработкой ошибок"""
        logger.info(f"Обновление астероидов (лимит: {limit if limit else 'все PHA'})")

        try:
            asteroids_data = await get_asteroid_data(limit=limit)
            if not asteroids_data:
                logger.warning("Нет данных об астероидах")
                return 0

            nasa_designations = [a.get('designation') for a in asteroids_data if a.get('designation')]

            count = 0
            for asteroid in asteroids_data:
                try:
                    designation = asteroid.get('designation')
                    if not designation:
                        logger.warning("Пропуск астероида без designation")
                        continue

                    data = {
                        'designation': designation,
                        'name': asteroid.get('name') or None,
                        'perihelion_au': self._safe_float_conversion(asteroid.get('perihelion_au')),
                        'aphelion_au': self._safe_float_conversion(asteroid.get('aphelion_au')),
                        'earth_moid_au': self._safe_float_conversion(asteroid.get('earth_moid_au')),
                        'absolute_magnitude': self._safe_float_conversion(
                            asteroid.get('absolute_magnitude'), default=18.0
                        ),
                        'estimated_diameter_km': self._safe_float_conversion(
                            asteroid.get('estimated_diameter_km'), default=0.0
                        ),
                        'accurate_diameter': bool(asteroid.get('accurate_diameter', False)),
                        'albedo': self._safe_float_conversion(asteroid.get('albedo'), default=0.15),
                        'orbit_class': asteroid.get('orbit_class') or 'Unknown',
                        'orbit_id': asteroid.get('orbit_id') or None,
                        'diameter_source': asteroid.get('diameter_source') or 'calculated'
                    }

                    existing = await self.asteroid_service.get_by_designation(designation)
                    if existing:
                        await self.asteroid_service.update(existing['id'], data)
                    else:
                        await self.asteroid_service.create(data)

                    count += 1

                except Exception as e:
                    logger.error(f"Ошибка обработки астероида {designation}: {e}")
                    continue

            if nasa_designations:
                deleted = await self.asteroid_service.delete_asteroids_not_in_designations(nasa_designations)
                if deleted > 0:
                    logger.info(f"Удалено {deleted} астероидов, отсутствующих в NASA API")

            logger.info(f"Успешно обновлено астероидов: {count}")
            return count

        except Exception as e:
            logger.error(f"Критическая ошибка обновления астероидов: {e}")
            return 0

    def _safe_float_conversion(self, value, default=0.0):
        """Безопасное преобразование значения в float"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    async def update_approaches(self, days: int = 3650) -> int:
        """Обновление сближений"""
        logger.info(f"Обновление сближений на {days} дней")
        try:
            asteroids_dicts = await self.asteroid_service.get_all(skip=0, limit=10000)
            if not asteroids_dicts:
                return 0

            approaches_data = await get_current_close_approaches(
                asteroids=asteroids_dicts,
                days=days,
                max_distance_au=0.05
            )
            if not approaches_data:
                return 0

            asteroid_dict = {a['designation']: a for a in asteroids_dicts if a.get('designation')}
            count = 0

            for approach in approaches_data:
                designation = approach.get('asteroid_designation')
                if not designation:
                    continue
                asteroid = asteroid_dict.get(designation)
                if not asteroid:
                    continue

                approach['asteroid_id'] = asteroid['id']

                existing = await self.approach_service.filter(
                    filters={'asteroid_id': asteroid['id'], 'approach_time': approach['approach_time']},
                    limit=1
                )
                if existing:
                    await self.approach_service.update(existing[0]['id'], approach)
                else:
                    await self.approach_service.create(approach)
                count += 1

            # Удаляем только прошлые сближения (старше текущей даты)
            cutoff_date = datetime.now()
            deleted = await self.approach_service.delete_old_approaches(cutoff_date)
            if deleted > 0:
                logger.info(f"Удалено {deleted} прошлых сближений")

            logger.info(f"Обновлено сближений: {count}")
            return count
        except Exception as e:
            logger.error(f"Ошибка обновления сближений: {e}")
            return 0

    async def update_threats(self) -> int:
        """Обновление угроз"""
        logger.info("Обновление оценок угроз")

        try:
            threats_data = await get_all_threats()
            if not threats_data:
                logger.warning("Нет данных об угрозах")
                from sqlalchemy import delete
                from domains.threat import ThreatAssessmentModel

                async with UnitOfWork(self.asteroid_service.session_factory) as uow:
                    query = delete(ThreatAssessmentModel)
                    result = await uow.session.execute(query)
                    await uow.session.commit()
                    deleted = result.rowcount

                if deleted > 0:
                    logger.info(f"Удалено {deleted} угроз (нет данных от NASA)")
                return 0

            asteroids_dicts = await self.asteroid_service.get_all(skip=0, limit=10000)
            asteroid_dict = {a['designation']: a for a in asteroids_dicts if a.get('designation')}

            nasa_designations = [t.get('designation') for t in threats_data if t.get('designation')]

            count = 0
            for threat in threats_data:
                try:
                    designation = threat.get('designation')
                    if not designation:
                        continue

                    asteroid = asteroid_dict.get(designation)
                    if not asteroid:
                        continue

                    threat['asteroid_id'] = asteroid['id']

                    existing = await self.threat_service.get_by_designation(designation)
                    if existing:
                        await self.threat_service.update(existing['id'], threat)
                    else:
                        await self.threat_service.create(threat)

                    count += 1

                except Exception as e:
                    logger.error(f"Ошибка обработки угрозы для {designation}: {e}")
                    continue

            # Удаляем угрозы которых нет в текущем списке NASA
            if nasa_designations:
                deleted = await self.threat_service.delete_threats_not_in_designations(nasa_designations)
                if deleted > 0:
                    logger.info(f"Удалено {deleted} угроз, отсутствующих в NASA API")

            # Удаляем угрозы с истёкшими годами риска
            current_year = datetime.now().year
            deleted_expired = await self.threat_service.delete_threats_with_expired_years(current_year)
            if deleted_expired > 0:
                logger.info(f"Удалено {deleted_expired} угроз с истёкшими годами риска")

            logger.info(f"Обновлено угроз: {count}")
            return count

        except Exception as e:
            logger.error(f"Ошибка обновления угроз: {e}")
            return 0

    async def update_all(self) -> dict:
        """Полное обновление всех данных"""
        logger.info("Запуск полного обновления данных")
        start_time = datetime.now()

        asteroids = await self.update_asteroids(limit=None)
        approaches = await self.update_approaches(days=3650)
        threats = await self.update_threats()

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"Обновление завершено за {duration:.2f} сек")
        logger.info(f"Астероиды: {asteroids}, Сближения: {approaches}, Угрозы: {threats}")

        return {
            "asteroids": asteroids,
            "approaches": approaches,
            "threats": threats,
            "duration_seconds": duration
        }