# get_data.py
"""
Асинхронные функции для получения данных об астероидах.
Основной интерфейс для работы с NASA SBDB API.
"""
import logging
from typing import List, Dict, Any, Optional
from external_apis.sbdb_api import NASASBDBClient

logger = logging.getLogger(__name__)

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