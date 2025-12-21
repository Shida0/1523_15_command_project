"""
Основные функции для получения данных об астероидах.
Упрощенный интерфейс для работы с NASA SBDB API.
"""
import logging
from typing import List, Dict, Any, Optional
from external_apis.sbdb_api import NASASBDBClient

logger = logging.getLogger(__name__)

def get_asteroid_data(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Основная функция для получения данных о потенциально опасных астероидах.
    
    Args:
        limit: Ограничение количества возвращаемых астероидов
        
    Returns:
        Список словарей с данными астероидов
    """
    try:
        client = NASASBDBClient()
        return client.get_asteroids(limit=limit)
    except Exception as e:
        logger.error(f"Ошибка получения данных об астероидах: {e}")
        return []