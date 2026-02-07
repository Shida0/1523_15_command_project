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
        """Обновление астероидов."""
        logger.info(f"Обновление астероидов (лимит: {limit})")
        
        try:
            # Получаем данные из NASA через utils.get_asteroid_data
            asteroids_data = await get_asteroid_data(limit=limit)
            
            if not asteroids_data:
                logger.warning("Нет данных об астероидах")
                return 0
            
            # Обновляем каждый астероид
            count = 0
            async with UnitOfWork(self.session_factory) as uow:
                for asteroid in asteroids_data:
                    designation = asteroid.get('designation')
                    if not designation:
                        continue
                    
                    # Форматируем данные для модели AsteroidModel
                    data = {
                        'designation': designation,
                        'name': asteroid.get('name'),
                        'perihelion_au': asteroid.get('perihelion_au'),
                        'aphelion_au': asteroid.get('aphelion_au'),
                        'earth_moid_au': asteroid.get('earth_moid_au'),
                        'absolute_magnitude': asteroid.get('absolute_magnitude', 0),
                        'estimated_diameter_km': asteroid.get('estimated_diameter_km', 0),
                        'accurate_diameter': asteroid.get('accurate_diameter', False),
                        'albedo': asteroid.get('albedo', 0.15),
                        'orbit_class': asteroid.get('orbit_class'),
                        'orbit_id': asteroid.get('orbit_id'),
                        'diameter_source': asteroid.get('diameter_source', 'calculated')
                    }
                    
                    # Проверяем существование
                    existing = await uow.asteroid_repo.get_by_designation(designation)
                    if existing:
                        # Update the existing asteroid
                        for key, value in data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        await uow.commit()
                    else:
                        # Create new asteroid
                        from domains.asteroid.models.asteroid import AsteroidModel
                        new_asteroid = AsteroidModel(**{k: v for k, v in data.items() 
                                                        if k in [col.name for col in AsteroidModel.__table__.columns] 
                                                        if k != 'id'})
                        uow.session.add(new_asteroid)
                        await uow.commit()
                    
                    count += 1
                
            logger.info(f"Обновлено астероидов: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Ошибка обновления астероидов: {e}")
            return 0
    
    async def update_approaches(self, days: int = 3650) -> int:
        """Обновление сближений."""
        logger.info(f"Обновление сближений на {days} дней")
        
        try:
            # Получаем астероиды из БД для передачи в get_current_close_approaches
            # Using UnitOfWork to fetch asteroids
            async with UnitOfWork(self.session_factory) as uow:
                asteroids = await uow.asteroid_repo.get_all(skip=0, limit=None)
                asteroids_dicts = [uow.asteroid_repo._model_to_dict(asteroid) for asteroid in asteroids]
                
            if not asteroids_dicts:
                logger.warning("Нет астероидов для обновления сближений")
                return 0
            
            # Получаем сближения через utils.get_current_close_approaches
            approaches_data = await get_current_close_approaches(
                asteroids=asteroids_dicts,
                days=days,
                max_distance_au=0.05
            )
            
            if not approaches_data:
                logger.warning("Нет данных о сближениях")
                return 0
            
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
            async with UnitOfWork(self.session_factory) as uow:
                asteroids = await uow.asteroid_repo.get_all(skip=0, limit=None)
                asteroids_dicts = [uow.asteroid_repo._model_to_dict(asteroid) for asteroid in asteroids]
            
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