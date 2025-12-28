# get_approaches.py
"""
Асинхронные функции для получения данных о сближениях.
Основной интерфейс для работы с NASA CAD API.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from external_apis.cad_api import CADClient

logger = logging.getLogger(__name__)

async def get_current_close_approaches(
    asteroids: List[Dict[str, Any]], 
    days: int = 3650, 
    max_distance_au: float = 0.05
) -> List[Dict[str, Any]]:
    """Получает все сближения астероидов с Землей на указанный период.
    
    Args:
        asteroids: Список астероидов для поиска сближений
        days: Количество дней от текущей даты для поиска сближений
        max_distance_au: Максимальное расстояние сближения в а.е.
        
    Returns:
        Список сближений, отсортированный по расстоянию
        
    Example:
        asteroids = await get_asteroid_data()
        approaches = await get_current_close_approaches(asteroids, days=3650)
        
    Note:
        Функция фильтрует сближения только для указанных астероидов
    """
    try:
        # Собираем обозначения астероидов
        asteroid_ids = [str(a.get('designation', '')) for a in asteroids if a.get('designation')]
        
        # Получаем сближения через CAD API
        async with CADClient() as client:
            all_approaches = await client.get_close_approaches(
                asteroid_ids=asteroid_ids,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days),
                max_distance_au=max_distance_au
            )
            
        # Преобразуем в плоский список
        flat_approaches = []
        for approaches in all_approaches.values():
            for approach in approaches:
                if approach.get('approach_time'):
                    flat_approaches.append(approach)
                    
        # Сортируем по расстоянию
        flat_approaches.sort(key=lambda x: x['distance_au'])
        
        logger.info(f"Найдено {len(flat_approaches)} сближений")
        return flat_approaches
        
    except Exception as e:
        logger.error(f"Ошибка получения сближений: {e}")
        return []
