from astroquery.jplhorizons import Horizons
from datetime import datetime, timedelta
import time
import logging

from .space_math import *

logger = logging.getLogger(__name__)

def get_current_close_approaches(data: list, days: int = 30) -> list:
    """
    Получает астероиды, которые реально приближаются к Земле в ближайшие дни.
    """
    close_approaches = []
    
    asteroids = [a for a in data if a.get('is_pha')]
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    logger.info(f"Запрашиваемый период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    
    for asteroid in asteroids:
        try:
            logger.info(f"Обрабатывается {asteroid['name']}...")
            
            asteroid_id = str(asteroid.get('number', asteroid.get('mpc_number', 'unknown')))
            
            obj = Horizons(
                id=asteroid_id,
                location='399',
                id_type='smallbody',
                epochs={
                    "start": start_date.strftime('%Y-%m-%d %H:%M'),
                    "stop": end_date.strftime('%Y-%m-%d %H:%M'),
                    "step": "1d"
                }
            )
            
            eph = obj.ephemerides()
            
            logger.info(f"Получены данные для {asteroid['name']}: {len(eph)} записей")
            
            # Проверяем наличие колонок
            has_delta_rate = 'delta_rate' in eph.colnames if hasattr(eph, 'colnames') else False
            
            for position in eph:
                distance_au = float(position['delta'])
                if distance_au < 0.05:
                    # Получение скорости
                    velocity = 0
                    if has_delta_rate:
                        try:
                            velocity = float(position['delta_rate'])
                        except (KeyError, ValueError):
                            velocity = 0
                    
                    approach_info = {
                        'asteroid': asteroid['name'],
                        'asteroid_number': asteroid.get('number'),
                        'approach_date': position['datetime_str'],
                        'distance_au': distance_au,
                        'distance_km': distance_au * 149597870.7,
                        'velocity_km_s': velocity,
                    }
                    close_approaches.append(approach_info)
            
            time.sleep(0.5)  # Уменьшенная задержка для тестов
                    
        except Exception as e:
            logger.error(f"Ошибка для астероида {asteroid.get('name', 'unknown')}: {e}")
            continue
    
    close_approaches.sort(key=lambda x: x['distance_au'])
    
    return close_approaches
