# get_approaches.py
"""
Асинхронные функции для получения данных о сближениях.
Основной интерфейс для работы с NASA CAD API.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ...external_api.clients.cad_api import CADClient
from shared.resilience import circuit_breaker, NASA_API_CIRCUIT_CONFIG, bulkhead, CAD_BULKHEAD_CONFIG, timeout, NASA_API_TIMEOUTS

logger = logging.getLogger(__name__)

from shared.utils.error_handlers import nasa_cad_api_endpoint

@nasa_cad_api_endpoint
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
        # Проверяем входные данные
        if not asteroids:
            logger.warning("Пустой список астероидов для получения сближений")
            return []
        
        # Собираем обозначения астероидов
        designations = []
        for asteroid in asteroids:
            designation = asteroid.get('designation')
            if designation and designation not in designations:
                designations.append(designation)
        
        if not designations:
            logger.warning("Нет валидных обозначений астероидов")
            return []
        
        logger.info(f"Запрос сближений для {len(designations)} астероидов")
        
        # Получаем сближения через CAD API
        async with CADClient() as client:
            all_approaches = await client.get_close_approaches(
                asteroid_ids=designations,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days),
                max_distance_au=max_distance_au
            )
        
        # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: проверяем формат возвращаемых данных
        if not all_approaches:
            logger.info("CAD API вернул пустые данные о сближениях")
            return []
        
        # Преобразуем в плоский список
        flat_approaches = []
        try:
            if isinstance(all_approaches, dict):
                for designation, approaches in all_approaches.items():
                    if isinstance(approaches, list):
                        for approach in approaches:
                            if isinstance(approach, dict):
                                approach['asteroid_designation'] = designation
                                flat_approaches.append(approach)
            elif isinstance(all_approaches, list):
                flat_approaches = all_approaches
        
            # Сортируем по расстоянию
            flat_approaches.sort(key=lambda x: x.get('distance_au', float('inf')))
        
            logger.info(f"Найдено {len(flat_approaches)} сближений")
            return flat_approaches
            
        except Exception as parse_error:
            logger.error(f"Ошибка парсинга данных сближений: {parse_error}")
            logger.debug(f"Данные: {all_approaches}")
            return []
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка получения сближений: {e}")
        return []  # Всегда возвращаем список
