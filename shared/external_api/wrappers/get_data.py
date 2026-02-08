# get_data.py
"""
Асинхронные функции для получения данных об астероидах.
Основной интерфейс для работы с NASA SBDB API.
"""
import logging
from typing import List, Dict, Any, Optional
from ...external_api.clients.sbdb_api import NASASBDBClient
from shared.resilience import circuit_breaker, NASA_API_CIRCUIT_CONFIG, bulkhead, SBDB_BULKHEAD_CONFIG, timeout, NASA_API_TIMEOUTS
from shared.utils.error_handlers import retry_with_exponential_backoff

logger = logging.getLogger(__name__)

@retry_with_exponential_backoff(max_attempts=3)
async def get_asteroid_data(limit: int|None = None) -> list:
    """Получение данных об астероидах с обработкой ошибок"""
    try:
        from shared.external_api.clients.sbdb_api import NASASBDBClient
        
        async with NASASBDBClient() as client:
            asteroids = await client.get_asteroids(limit=limit)
            
            # Проверка обязательных полей (designation)
            valid_asteroids = []
            for asteroid in asteroids:
                if asteroid and isinstance(asteroid, dict) and 'designation' in asteroid and asteroid['designation']:
                    # Преобразование типов для числовых значений
                    for key, value in asteroid.items():
                        if value is None:
                            continue
                        # Проверяем, нужно ли преобразовать в число
                        if key in ['absolute_magnitude', 'estimated_diameter_km', 'earth_moid_au', 
                                  'perihelion_au', 'aphelion_au', 'albedo']:
                            try:
                                if isinstance(value, str):
                                    asteroid[key] = float(value)
                                elif not isinstance(value, (int, float)):
                                    asteroid[key] = float(value)
                            except (ValueError, TypeError):
                                # Если не удается преобразовать, устанавливаем значение по умолчанию
                                if key == 'albedo':
                                    asteroid[key] = 0.15
                                elif key in ['absolute_magnitude', 'estimated_diameter_km', 'earth_moid_au', 
                                           'perihelion_au', 'aphelion_au']:
                                    asteroid[key] = 0.0
                                else:
                                    asteroid[key] = None
                    
                    valid_asteroids.append(asteroid)
                else:
                    logger.warning(f"Пропуск астероида без designation: {asteroid}")
            
            logger.info(f"Получено {len(valid_asteroids)} валидных астероидов из {len(asteroids)}")
            
            return valid_asteroids
            
    except Exception as e:
        logger.error(f"Ошибка получения данных об астероидах: {e}")
        return []  # Всегда возвращай пустой список при ошибке