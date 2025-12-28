# get_treat.py
"""
Асинхронные функции для получения данных об угрозах.
Основной интерфейс для работы с NASA Sentry API.
"""
import logging
from typing import List, Dict, Any, Optional
from external_apis.sentry_api import SentryClient

logger = logging.getLogger(__name__)

async def get_all_treats() -> List[Dict[str, Any]]:
    """Получает все актуальные угрозы столкновения с Землей.
    
    Returns:
        Список объектов с данными об угрозах
        
    Example:
        threats = await get_all_treats()
        
    Note:
        Возвращает только объекты с ненулевой оценкой по Туринской шкале (ts_max > 0)
    """
    try:
        async with SentryClient() as client:
            risks = await client.fetch_current_impact_risks()
            
            # ФИКС: Проверяем, есть ли данные перед преобразованием
            if not risks:
                logger.info("Нет данных об угрозах от Sentry API")
                return []
                
            # Преобразуем в словари
            result = []
            for risk in risks:
                # ФИКС: Проверяем, есть ли метод to_dict
                if hasattr(risk, 'to_dict'):
                    result.append(risk.to_dict())
                else:
                    # Альтернативное преобразование для отладки
                    logger.debug(f"Угроза без метода to_dict: {risk}")
                    # Создаем словарь вручную
                    risk_dict = {
                        'designation': getattr(risk, 'designation', 'Неизвестно'),
                        'fullname': getattr(risk, 'fullname', ''),
                        'impact_probability': getattr(risk, 'ip', 0.0),
                        'torino_scale': getattr(risk, 'ts_max', 0),
                        'diameter_km': getattr(risk, 'diameter', 0.05),
                        'velocity_km_s': getattr(risk, 'v_inf', 20.0),
                        'absolute_magnitude': getattr(risk, 'h', 22.0),
                    }
                    result.append(risk_dict)
                    
            logger.info(f"Получено {len(result)} угроз от Sentry API")
            return result
            
    except IndexError as e:
        # ФИКС: Конкретная обработка ошибки индекса
        logger.error(f"Ошибка индекса при получении угроз: {e}. Возможно, Sentry API вернул пустой список.")
        return []
    except Exception as e:
        logger.error(f"Ошибка получения данных об угрозах: {e}")
        return []
        
async def get_treat_details(designation: str) -> Optional[Dict[str, Any]]:
    """Получает детальную информацию об угрозе для конкретного астероида.
    
    Args:
        designation: Обозначение астероида (например, "2023 DW")
        
    Returns:
        Словарь с детальной информацией или None, если объект не найден
        
    Example:
        details = await get_treat_details("2023 DW")
    """
    try:
        async with SentryClient() as client:
            risk = await client.fetch_object_details(designation)
            return risk.to_dict() if risk and hasattr(risk, 'to_dict') else risk
    except Exception as e:
        logger.error(f"Ошибка получения деталей угрозы: {e}")
        return None