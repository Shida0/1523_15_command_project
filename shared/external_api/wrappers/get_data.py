# get_data.py
"""
Асинхронные функции для получения данных об астероидах.
Основной интерфейс для работы с NASA SBDB API.
"""
import logging
from typing import List, Dict, Any, Optional
from domains.external_api.clients.sbdb_api import NASASBDBClient
from shared.resilience import circuit_breaker, NASA_API_CIRCUIT_CONFIG, bulkhead, SBDB_BULKHEAD_CONFIG, timeout, NASA_API_TIMEOUTS

logger = logging.getLogger(__name__)

@circuit_breaker(NASA_API_CIRCUIT_CONFIG)
@bulkhead(SBDB_BULKHEAD_CONFIG)
@timeout(NASA_API_TIMEOUTS['sbdb'])
async def get_asteroid_data(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Получает данные о потенциально опасных астероидах (PHA).
    
    Args:
        limit: Ограничение количества возвращаемых астероидов
        
    Returns:
        Список словарей с данными астероидов в формате AsteroidModel
        
    Example:
        asteroids = await get_asteroid_data(limit=100)
        
    Note:
        Функция использует асинхронный клиент NASASBDBClient
    """
    try:
        async with NASASBDBClient() as client:
            return await client.get_asteroids(limit=limit)
    except Exception as e:
        logger.error(f"Ошибка получения данных об астероидах: {e}")
        return []