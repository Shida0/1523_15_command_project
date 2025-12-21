"""
Основные функции для получения данных об угрозах и сближениях.
Упрощенный интерфейс для работы с Sentry API.
"""
import logging
from typing import List, Dict, Any, Optional
from external_apis.sentry_api import SentryClient

logger = logging.getLogger(__name__)

def get_all_treats() -> List[Dict[str, Any]]:
    """
    Получить все актуальные сближения с Землей (объекты с ненулевым ts_max).
        
    Returns:
        Список словарей с данными о сближениях
    """
    try:
        return SentryClient().fetch_current_impact_risks()
    except Exception as e:
        logger.error(f"Ошибка получения данных о сближениях: {e}")
        return []

def get_treat_details(designation: str) -> Dict[str, Any]:
    """
    Получить детальную информацию о конкретном сближении.
    
    Args:
        designation: Обозначение астероида (например, "2023 DW")
        
    Returns:
        Словарь с детальной информацией о сближении
    """
    try:
        return SentryClient().fetch_object_details(designation)
    except Exception as e:
        logger.error(f"Ошибка получения деталей сближения: {e}")
        return {
            "designation": designation,
            "error": str(e),
            "status": "Ошибка при получении данных"
        }