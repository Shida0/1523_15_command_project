# file name: monitoring.py (обновленная версия)
"""
Мониторинг сближений астероидов с Землей.
Использует комбинированный подход: CAD API или SBDB+Skyfield.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from .cad_api import CombinedCADClient

logger = logging.getLogger(__name__)

def get_current_close_approaches(data, days=3650, max_distance_au=0.05):
    # Собираем ID всех PHA астероидов
    asteroids = [a for a in data if a.get('is_pha', False)]
    asteroid_ids = [str(a.get('mpc_number') or a.get('designation', '')) for a in asteroids]
    
    # Используем bulk-запрос
    client = CombinedCADClient()
    all_approaches = client.get_close_approaches(
        asteroid_ids=asteroid_ids,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=days),
        max_distance_au=max_distance_au
    )
    
    flat_approaches = []
    for asteroid_des, approaches in all_approaches.items():
        for approach in approaches:
            # КРИТИЧЕСКАЯ ПРОВЕРКА
            if approach['approach_time'] is None:
                logger.error("Обнаружена запись с approach_time=None для астероида %s. Пропускаем.", asteroid_des)
                continue
            flat_approaches.append(approach)
    
    # Сортируем по расстоянию
    flat_approaches.sort(key=lambda x: x['distance_au'])
    
    return flat_approaches
