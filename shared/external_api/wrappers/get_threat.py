# get_threat.py
import logging
from typing import List, Dict, Any, Optional
from ...external_api.clients.sentry_api import SentryClient, SentryImpactRisk


logger = logging.getLogger(__name__)

async def get_all_threats() -> List[Dict[str, Any]]:
    """Получает все актуальные угрозы столкновения с Землей"""
    try:
        async with SentryClient() as client:
            risks = await client.fetch_current_impact_risks()

            if not risks:
                logger.info("Нет данных об угрозах от Sentry API (список пуст)")
                return []

            result = []
            for risk in risks:
                if isinstance(risk, SentryImpactRisk):
                    try:
                        result.append(risk.to_dict())
                    except AttributeError:
                        logger.warning(f"У объекта угрозы отсутствует метод to_dict, создаем словарь вручную")
                        result.append(_impact_risk_to_dict(risk))
                else:
                    logger.warning(f"Получен объект неожиданного типа {type(risk)}. Пропускаем.")

            logger.info(f"Успешно получено и преобразовано {len(result)} угроз от Sentry API")
            return result

    except RuntimeError as e:
        logger.error(f"Ошибка при работе с SentryClient: {e}")
        return []
    except IndexError as e:
        logger.error(f"Ошибка индекса при обработке данных от Sentry API: {e}. Возможно, структура ответа неожиданная.")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка получения данных об угрозах: {e}", exc_info=True)
        return []


def _impact_risk_to_dict(risk: SentryImpactRisk) -> Dict[str, Any]:
    """Создает словарь из объекта SentryImpactRisk (резервный метод)"""
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