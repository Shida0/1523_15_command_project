from astroquery.jplhorizons import Horizons
from datetime import datetime, timedelta
import time
import logging

from .space_math import *

logger = logging.Logger(__name__)

def get_current_close_approaches(data: list, days: int = 30) -> list:
    """
    Получает астероиды, которые реально приближаются к Земле в ближайшие дни.
    
    Args:
        data: Список данных об астероидах
        days: Количество дней для анализа (по умолчанию 30)
    
    Returns:
        list: Список словарей с данными о близких сближениях
    """
    close_approaches = []
    
    # фильтруем только потенциально опасные астероиды
    asteroids = [a for a in data if a.get('is_pha')]
    
    # время нынешнее и через N дней
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    logger.info(f"Запрашиваемый период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    
    # проходимся по всем потенциально опасным астероидам
    for asteroid in asteroids:
        try:
            logger.info(f"Обрабатывается {asteroid['name']}...")
            
            # Смотрим на астероид в период времени от нынешнего момента до того, который будет через N дней
            obj = Horizons(
                id=str(asteroid['number']),
                location='399',
                id_type=None,
                epochs={
                    "start": start_date.strftime('%Y-%m-%d'),
                    "stop": end_date.strftime('%Y-%m-%d'),
                    "step": "1d"
                }
            )
            
            # Получаем эфемериды для реального временного периода
            eph = obj.ephemerides()
            
            logger.info(f"Получены данные для {asteroid['name']}: {len(eph)} записей")
            
            # Ищем близкие подходы с порогом 0.05 а.е.
            for position in eph:
                distance_au = float(position['delta'])
                if distance_au < 0.05:
                    approach_info = {
                        'asteroid': asteroid['name'],
                        'asteroid_number': asteroid['number'],
                        'approach_date': position['datetime_str'],
                        'distance_au': distance_au,
                        'distance_km': distance_au * 149597870.7,
                        'velocity_km_s': float(position['delta_rate']) if 'delta_rate' in position.colnames else 0,
                    }
                    close_approaches.append(approach_info)
            
            # Задержка чтобы не перегружать сервер
            time.sleep(2)
                    
        except Exception as e:
            logger.error(f"Ошибка для астероида {asteroid.get('name', asteroid['number'])}: {e}")
            continue
    
    # Сортируем по расстоянию (от ближайшего к дальнему)
    close_approaches.sort(key=lambda x: x['distance_au'])
    
    return close_approaches

