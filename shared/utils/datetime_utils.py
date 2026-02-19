"""
Утилиты для безопасной работы с датами и временем.
Решает проблему смешения aware/naive datetime при работе с PostgreSQL.
"""
from datetime import datetime, timezone
from typing import Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

def ensure_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Преобразует aware datetime в naive UTC datetime.
    Если datetime уже naive, возвращает как есть.
    
    Args:
        dt: datetime (может быть aware или naive)
        
    Returns:
        naive datetime в UTC или None
        
    Пример:
        aware_dt = datetime.now(timezone.utc)  # aware
        naive_dt = ensure_naive_utc(aware_dt)  # naive UTC
    """
    if dt is None:
        return None
    
    if dt.tzinfo is not None:
        # Преобразуем aware datetime в naive UTC
        naive_dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        logger.debug(f"Преобразовано aware datetime в naive UTC: {dt} -> {naive_dt}")
        return naive_dt
    
    # Уже naive, возвращаем как есть
    return dt

def ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Преобразует naive datetime в aware UTC datetime.
    Если datetime уже aware, возвращает как есть (предполагается UTC).
    
    Args:
        dt: datetime (может быть aware или naive)
        
    Returns:
        aware datetime в UTC или None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Добавляем часовой пояс UTC к naive datetime
        aware_dt = dt.replace(tzinfo=timezone.utc)
        logger.debug(f"Преобразовано naive datetime в aware UTC: {dt} -> {aware_dt}")
        return aware_dt
    
    # Уже aware, предполагаем UTC
    if dt.tzinfo != timezone.utc:
        # Конвертируем в UTC, если другой часовой пояс
        aware_dt = dt.astimezone(timezone.utc)
        logger.debug(f"Конвертировано в UTC: {dt} -> {aware_dt}")
        return aware_dt
    
    return dt

def normalize_datetime(value: Any) -> Any:
    """
    Рекурсивно нормализует datetime значения в структурах данных.
    Преобразует все aware datetime в naive UTC для работы с БД.
    
    Args:
        value: Любое значение (datetime, список, словарь, etc.)
        
    Returns:
        Значение с нормализованными datetime
    """
    if isinstance(value, datetime):
        return ensure_naive_utc(value)
    
    elif isinstance(value, list):
        return [normalize_datetime(item) for item in value]
    
    elif isinstance(value, dict):
        return {key: normalize_datetime(val) for key, val in value.items()}
    
    else:
        return value

def current_naive_utc() -> datetime:
    """
    Возвращает текущее время как naive datetime в UTC.
    Используется для фильтров и условий в БД.
    
    Returns:
        naive datetime в UTC
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

def current_aware_utc() -> datetime:
    """
    Возвращает текущее время как aware datetime в UTC.
    Используется для бизнес-логики.
    
    Returns:
        aware datetime в UTC
    """
    return datetime.now(timezone.utc)

# Алиасы для удобства
to_naive = ensure_naive_utc
to_aware = ensure_aware_utc
now_naive = current_naive_utc
now_aware = current_aware_utc