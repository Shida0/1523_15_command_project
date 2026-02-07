# get_treat.py (исправленная версия)
"""
Асинхронные функции для получения данных об угрозах.
Основной интерфейс для работы с NASA Sentry API.
"""
import logging
from typing import List, Dict, Any, Optional
from domains.external_api.clients.sentry_api import SentryClient, SentryImpactRisk
from shared.resilience import circuit_breaker, NASA_API_CIRCUIT_CONFIG, bulkhead, SENTRY_BULKHEAD_CONFIG, timeout, NASA_API_TIMEOUTS

logger = logging.getLogger(__name__)

@circuit_breaker(NASA_API_CIRCUIT_CONFIG)
@bulkhead(SENTRY_BULKHEAD_CONFIG)
@timeout(NASA_API_TIMEOUTS['sentry'])
async def get_all_treats() -> List[Dict[str, Any]]:
    """Получает все актуальные угрозы столкновения с Землей.
    
    Returns:
        Список словарей с данными об угрозах.
        Возвращает пустой список в случае ошибки или отсутствия данных.
    """
    try:
        async with SentryClient() as client:
            # Этот метод может выбросить исключение, поэтому оборачиваем
            risks = await client.fetch_current_impact_risks()
            
            if not risks:
                logger.info("Нет данных об угрозах от Sentry API (список пуст)")
                return []
                
            # Преобразуем в словари
            result = []
            for risk in risks:
                # Убеждаемся, что risk - это экземпляр SentryImpactRisk
                if isinstance(risk, SentryImpactRisk):
                    try:
                        result.append(risk.to_dict())
                    except AttributeError:
                        # Резервное создание словаря, если метод to_dict отсутствует
                        logger.warning(f"У объекта угрозы отсутствует метод to_dict, создаем словарь вручную")
                        result.append(_impact_risk_to_dict(risk))
                else:
                    logger.warning(f"Получен объект неожиданного типа {type(risk)}. Пропускаем.")
                    
            logger.info(f"Успешно получено и преобразовано {len(result)} угроз от Sentry API")
            return result
            
    except RuntimeError as e:
        # Ошибка клиента Sentry (например, проблема сети или API)
        logger.error(f"Ошибка при работе с SentryClient: {e}")
        return []
    except IndexError as e:
        logger.error(f"Ошибка индекса при обработке данных от Sentry API: {e}. Возможно, структура ответа неожиданная.")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка получения данных об угрозах: {e}", exc_info=True)
        return []
        
@circuit_breaker(NASA_API_CIRCUIT_CONFIG)
@bulkhead(SENTRY_BULKHEAD_CONFIG)
@timeout(NASA_API_TIMEOUTS['sentry'])
async def get_treat_details(designation: str) -> Optional[Dict[str, Any]]:
    """Получает детальную информацию об угрозе для конкретного астероида.
    
    Args:
        designation: Обозначение астероида (например, "2023 DW")
        
    Returns:
        Словарь с детальной информацией или None, если объект не найден или произошла ошибка.
    """
    try:
        async with SentryClient() as client:
            risk = await client.fetch_object_details(designation)
            
            # Явная проверка на None и корректный тип
            if risk is None:
                logger.info(f"Объект {designation} не найден или отсутствует в Sentry")
                return None
                
            if not isinstance(risk, SentryImpactRisk):
                logger.warning(f"Для объекта {designation} получен неожиданный тип данных: {type(risk)}")
                return None
                
            try:
                return risk.to_dict()
            except AttributeError:
                logger.warning(f"У объекта {designation} отсутствует метод to_dict, создаем словарь вручную")
                return _impact_risk_to_dict(risk)
                
    except RuntimeError as e:
        logger.error(f"Ошибка SentryClient при запросе объекта {designation}: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка получения деталей угрозы для {designation}: {e}")
        return None

def _impact_risk_to_dict(risk: SentryImpactRisk) -> Dict[str, Any]:
    """Создает словарь из объекта SentryImpactRisk (резервный метод).
    
    Используется, если у объекта отсутствует метод to_dict.
    """
    # Простой способ, использующий публичные атрибуты датакласса
    return {
        'designation': risk.designation,
        'fullname': risk.fullname,
        'impact_probability': risk.ip,
        'torino_scale': risk.ts_max,
        'palermo_scale': risk.ps_max,
        'diameter_km': risk.diameter,
        'velocity_km_s': risk.v_inf,
        'absolute_magnitude': risk.h,
        'n_imp': risk.n_imp,
        'impact_years': risk.impact_years,
        'last_obs': risk.last_obs,
        'threat_level_ru': risk.threat_level_ru,
        'torino_scale_ru': risk.torino_scale_ru,
        'impact_probability_text_ru': risk.impact_probability_text_ru,
        'last_update': risk.last_update.isoformat() if hasattr(risk.last_update, 'isoformat') else str(risk.last_update)
    }