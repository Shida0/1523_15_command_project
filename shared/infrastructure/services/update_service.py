"""
сервис для обновления данных в БД.
"""
import logging
from datetime import datetime
from typing import Optional

from domains.asteroid.services.asteroid_service import AsteroidService
from domains.approach.services.approach_service import ApproachService
from domains.threat.services.threat_service import ThreatService
from shared.external_api.wrappers.get_data import get_asteroid_data
from shared.external_api.wrappers.get_approaches import get_current_close_approaches
from shared.external_api.wrappers.get_threat import get_all_treats

logger = logging.getLogger(__name__)


class UpdateService:
    """
    Сервис для периодического обновления данных из NASA API.
    """

    def __init__(self, session_factory):
        """
        Инициализация сервиса обновления.

        Args:
            session_factory: Фабрика для создания сессий SQLAlchemy
        """
        self.session_factory = session_factory

        # Инициализируем сервисы с фабрикой сессий
        self.asteroid_service = AsteroidService(session_factory)
        self.approach_service = ApproachService(session_factory)
        self.threat_service = ThreatService(session_factory)

        logger.info("UpdateService инициализирован")

    async def update_asteroids(self, limit: Optional[int] = 500) -> int:
        """Обновление астероидов с надёжной обработкой ошибок"""
        logger.info(f"Обновление астероидов (лимит: {limit})")

        try:
            asteroids_data = await get_asteroid_data(limit=limit)
            if not asteroids_data:
                logger.warning("Нет данных об астероидах")
                return 0

            count = 0
            for asteroid in asteroids_data:
                try:
                    designation = asteroid.get('designation')
                    if not designation:
                        logger.warning("Пропуск астероида без designation")
                        continue

                    # Подготовка данных
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

                    # Проверяем существование астероида
                    existing = await self.asteroid_service.get_by_designation(designation)
                    if existing:
                        # Обновляем существующий
                        await self.asteroid_service.update(existing['id'], data)
                    else:
                        # Создаём новый
                        await self.asteroid_service.create(data)

                    count += 1

                except Exception as e:
                    logger.error(f"Ошибка обработки астероида {designation}: {e}")
                    continue  

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
        logger.info(f"Обновление сближений на {days} дней")
        try:
            asteroids_dicts = await self.asteroid_service.get_all(skip=0, limit=1000)
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

                # Поиск существующего сближения
                existing = await self.approach_service.filter(
                    filters={'asteroid_id': asteroid['id'], 'approach_time': approach['approach_time']},
                    limit=1
                )
                if existing:
                    # Обновляем
                    await self.approach_service.update(existing[0]['id'], approach)
                else:
                    # Создаём
                    await self.approach_service.create(approach)
                count += 1

            logger.info(f"Обновлено сближений: {count}")
            return count
        except Exception as e:
            logger.error(f"Ошибка обновления сближений: {e}")
            return 0

        except Exception as e:
            logger.error(f"Ошибка обновления сближений: {e}")
            return 0

    async def update_threats(self) -> int:
        """Обновление угроз."""
        logger.info("Обновление оценок угроз")

        try:
            threats_data = await get_all_treats()
            if not threats_data:
                logger.warning("Нет данных об угрозах")
                return 0

            # Получаем астероиды для связи
            asteroids_dicts = await self.asteroid_service.get_all(skip=0, limit=None)
            asteroid_dict = {a['designation']: a for a in asteroids_dicts if a.get('designation')}

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

                    # Проверяем существование угрозы
                    existing = await self.threat_service.get_by_designation(designation)
                    if existing:
                        await self.threat_service.update(existing['id'], threat)
                    else:
                        await self.threat_service.create(threat)

                    count += 1

                except Exception as e:
                    logger.error(f"Ошибка обработки угрозы для {designation}: {e}")
                    continue

            logger.info(f"Обновлено угроз: {count}")
            return count

        except Exception as e:
            logger.error(f"Ошибка обновления угроз: {e}")
            return 0

    async def update_all(self) -> dict:
        """Полное обновление всех данных."""
        logger.info("=== ЗАПУСК ПОЛНОГО ОБНОВЛЕНИЯ ===")
        start_time = datetime.now()

        # Обновляем данные
        asteroids = await self.update_asteroids(limit=100000)
        approaches = await self.update_approaches(days=3650)
        threats = await self.update_threats()

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"=== ОБНОВЛЕНИЕ ЗАВЕРШЕНО ===")
        logger.info(f"Время: {duration:.2f} сек")
        logger.info(f"Астероиды: {asteroids}, Сближения: {approaches}, Угрозы: {threats}")

        return {
            "asteroids": asteroids,
            "approaches": approaches,
            "threats": threats,
            "duration_seconds": duration
        }