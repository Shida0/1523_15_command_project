"""
Минималистичный сервис для обновления данных в БД.
Использует функции из utils/ для получения данных.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from domains.asteroid.services.asteroid_service import AsteroidService
from domains.approach.services.approach_service import ApproachService
from domains.threat.services.threat_service import ThreatService
from shared.external_api.wrappers.get_data import get_asteroid_data
from shared.external_api.wrappers.get_approaches import get_current_close_approaches
from shared.external_api.wrappers.get_threat import get_all_treats
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class UpdateService:
    """
    Сервис для периодического обновления данных из NASA API.
    Минималистичная реализация с использованием функций из utils.
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
    
    async def update_asteroids(self, limit: int|None = 500) -> int:
        """Обновление астероидов с надежной обработкой ошибок"""
        logger.info(f"Обновление астероидов (лимит: {limit})")
        
        try:
            # 1. Получение данных с обработкой ошибок
            asteroids_data = await get_asteroid_data(limit=limit)
            
            if not asteroids_data:
                logger.warning("Нет данных об астероидах")
                return 0
            
            # 2. Обновление в транзакции
            async with UnitOfWork(self.session_factory) as uow:
                count = 0
                
                for asteroid in asteroids_data:
                    try:
                        # Проверка наличия designation
                        designation = asteroid.get('designation')
                        if not designation:
                            logger.warning(f"Пропуск астероида без designation: {asteroid}")
                            continue
                        
                        # Преобразование None значений в дефолтные
                        # Проверка типов данных (float, int, str)
                        data = {
                            'designation': designation,
                            'name': asteroid.get('name') or None,
                            'perihelion_au': self._safe_float_conversion(asteroid.get('perihelion_au')),
                            'aphelion_au': self._safe_float_conversion(asteroid.get('aphelion_au')),
                            'earth_moid_au': self._safe_float_conversion(asteroid.get('earth_moid_au')),
                            'absolute_magnitude': self._safe_float_conversion(asteroid.get('absolute_magnitude'), default=18.0),
                            'estimated_diameter_km': self._safe_float_conversion(asteroid.get('estimated_diameter_km'), default=0.0),
                            'accurate_diameter': bool(asteroid.get('accurate_diameter', False)),
                            'albedo': self._safe_float_conversion(asteroid.get('albedo'), default=0.15),
                            'orbit_class': asteroid.get('orbit_class') or 'Unknown',
                            'orbit_id': asteroid.get('orbit_id') or None,
                            'diameter_source': asteroid.get('diameter_source') or 'calculated'
                        }
                        
                        # 3. Поиск существующего или создание нового
                        existing = await uow.asteroid_repo.get_by_designation(designation)
                        if existing:
                            # Обновление
                            for key, value in data.items():
                                if hasattr(existing, key):
                                    setattr(existing, key, value)
                        else:
                            # Создание
                            from domains.asteroid.models.asteroid import AsteroidModel
                            new_asteroid = AsteroidModel(**{k: v for k, v in data.items()
                                                            if k in [col.name for col in AsteroidModel.__table__.columns]
                                                            if k != 'id'})
                            uow.session.add(new_asteroid)
                        
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"Ошибка обработки астероида {designation}: {e}")
                        continue  # Продолжаем обработку остальных
                
                # 4. Коммит всех изменений
                await uow.commit()
                
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
        """Обновление сближений с улучшенной обработкой ошибок."""
        logger.info(f"Обновление сближений на {days} дней")
        
        try:
            # Получаем астероиды из БД для передачи в get_current_close_approaches
            asteroids_dicts = await self.asteroid_service.get_all(skip=0, limit=1000)  # Ограничиваем для теста
            logger.info(f"Получено {len(asteroids_dicts)} астероидов для поиска сближений")
            
            if not asteroids_dicts:
                logger.warning("Нет астероидов для обновления сближений")
                return 0

            # Получаем сближения
            approaches_data = await get_current_close_approaches(
                asteroids=asteroids_dicts,
                days=days,
                max_distance_au=0.05
            )
            
            # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: проверяем результат
            if not approaches_data:
                logger.info("Нет данных о сближениях в указанном периоде")
                return 0
            
            logger.info(f"Получено {len(approaches_data)} сближений для обработки")

            # Создаем словарь астероидов для быстрого поиска
            asteroid_dict = {a['designation']: a for a in asteroids_dicts if a.get('designation')}

            # Обновляем сближения
            count = 0
            async with UnitOfWork(self.session_factory) as uow:
                for approach in approaches_data:
                    designation = approach.get('asteroid_designation')
                    if not designation:
                        continue

                    # Находим астероид в словаре
                    asteroid = asteroid_dict.get(designation)
                    if not asteroid:
                        continue

                    approach['asteroid_id'] = asteroid['id']

                    # Ищем существующее сближение
                    existing_approaches = await uow.approach_repo.filter(
                        filters={'asteroid_id': asteroid['id']},
                        skip=0,
                        limit=1
                    )

                    if existing_approaches:
                        # Update existing approach
                        existing_approach = existing_approaches[0]
                        for key, value in approach.items():
                            if hasattr(existing_approach, key):
                                setattr(existing_approach, key, value)
                        await uow.commit()
                    else:
                        # Create new approach
                        from domains.approach.models.close_approach import CloseApproachModel
                        new_approach = CloseApproachModel(**{k: v for k, v in approach.items()
                                                           if k in [col.name for col in CloseApproachModel.__table__.columns]
                                                           if k != 'id'})
                        uow.session.add(new_approach)
                        await uow.commit()

                    count += 1

            logger.info(f"Обновлено сближений: {count}")
            return count

        except Exception as e:
            logger.error(f"Ошибка обновления сближений: {e}")
            return 0
    
    async def update_threats(self) -> int:
        """Обновление угроз."""
        logger.info("Обновление оценок угроз")
        
        try:
            # Получаем данные из Sentry через utils.get_all_treats
            threats_data = await get_all_treats()
            
            if not threats_data:
                logger.warning("Нет данных об угрозах")
                return 0
            
            # Получаем астероиды для связи
            asteroids_dicts = await self.asteroid_service.get_all(skip=0, limit=None)
            
            asteroid_dict = {a['designation']: a for a in asteroids_dicts if a.get('designation')}
            
            # Обновляем угрозы
            count = 0
            async with UnitOfWork(self.session_factory) as uow:
                for threat in threats_data:
                    designation = threat.get('designation')
                    if not designation:
                        continue
                    
                    # Находим астероид
                    asteroid = asteroid_dict.get(designation)
                    if not asteroid:
                        continue
                    
                    threat['asteroid_id'] = asteroid['id']
                    
                    # Ищем существующую угрозу
                    existing = await uow.threat_repo.get_by_designation(designation)
                    if existing:
                        # Update existing threat
                        for key, value in threat.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        await uow.commit()
                    else:
                        # Create new threat
                        from domains.threat.models.threat_assessment import ThreatAssessmentModel
                        new_threat = ThreatAssessmentModel(**{k: v for k, v in threat.items() 
                                                           if k in [col.name for col in ThreatAssessmentModel.__table__.columns] 
                                                           if k != 'id'})
                        uow.session.add(new_threat)
                        await uow.commit()
                    
                    count += 1
                
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
        asteroids = await self.update_asteroids(limit=1000)
        approaches = await self.update_approaches(days=3650)
        threats = await self.update_threats()
        
        # Рассчитываем время
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