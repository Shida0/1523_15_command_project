"""
Минималистичный сервис для обновления данных в БД.
Использует функции из utils/ для получения данных.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .asteroid_service import AsteroidService
from .approach_service import ApproachService
from .threat_service import ThreatService
from api_functions import get_asteroid_data, get_current_close_approaches, get_all_treats

logger = logging.getLogger(__name__)


class UpdateService:
    """
    Сервис для периодического обновления данных из NASA API.
    Минималистичная реализация с использованием функций из utils.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Инициализация сервиса обновления.
        
        Args:
            db_session: Сессия для работы с БД
        """
        self.session = db_session
        
        # Инициализируем сервисы
        self.asteroid_service = AsteroidService(db_session)
        self.approach_service = ApproachService(db_session)
        self.threat_service = ThreatService(db_session)
        
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
                existing = await self.asteroid_service.get_by_designation(designation)
                if existing:
                    await self.asteroid_service.update(existing['id'], data)
                else:
                    await self.asteroid_service.create(data)
                
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
            asteroids = await self.asteroid_service.get_all(limit=None)
            
            if not asteroids:
                logger.warning("Нет астероидов для обновления сближений")
                return 0
            
            # Получаем сближения через utils.get_current_close_approaches
            approaches_data = await get_current_close_approaches(
                asteroids=asteroids,
                days=days,
                max_distance_au=0.05
            )
            
            if not approaches_data:
                logger.warning("Нет данных о сближениях")
                return 0
            
            # Создаем словарь астероидов для быстрого поиска
            asteroid_dict = {a['designation']: a for a in asteroids if a.get('designation')}
            
            # Обновляем сближения
            count = 0
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
                existing = await self.approach_service.filter({
                    'asteroid_id': asteroid['id'],
                    'approach_time': approach.get('approach_time')
                })
                
                if existing:
                    await self.approach_service.update(existing[0]['id'], approach)
                else:
                    await self.approach_service.create(approach)
                
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
            asteroids = await self.asteroid_service.get_all(limit=None)
            asteroid_dict = {a['designation']: a for a in asteroids if a.get('designation')}
            
            # Обновляем угрозы
            count = 0
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
                existing = await self.threat_service.get_by_designation(designation)
                if existing:
                    await self.threat_service.update(existing['id'], threat)
                else:
                    await self.threat_service.create(threat)
                
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