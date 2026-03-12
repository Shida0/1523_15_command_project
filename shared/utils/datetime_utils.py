"""
Утилиты для безопасной работы с датами и временем.
Решает проблему смешения aware/naive datetime при работе с PostgreSQL.
"""
from datetime import datetime, timezone
from typing import Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

def ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Преобразует datetime в aware UTC.
    Если datetime naive – добавляет UTC.
    Если уже aware – конвертирует в UTC.
    
    Args:
        dt: datetime (может быть aware или naive)
        
    Returns:
        aware datetime в UTC или None
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # naive -> добавить UTC
        aware_dt = dt.replace(tzinfo=timezone.utc)
        logger.debug(f"Преобразовано naive datetime в aware UTC: {dt} -> {aware_dt}")
        return aware_dt
    # уже aware – конвертируем в UTC (на случай другой таймзоны)
    aware_dt = dt.astimezone(timezone.utc)
    if aware_dt != dt:
        logger.debug(f"Конвертировано в UTC: {dt} -> {aware_dt}")
    return aware_dt

def ensure_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Преобразует aware datetime в naive UTC.
    Если уже naive – возвращает как есть.
    
    Args:
        dt: datetime (может быть aware или naive)
        
    Returns:
        naive datetime в UTC или None
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # aware -> naive UTC
        naive_dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        logger.debug(f"Преобразовано aware datetime в naive UTC: {dt} -> {naive_dt}")
        return naive_dt
    return dt

def normalize_datetime(value: Any) -> Any:
    """
    Рекурсивно нормализует datetime значения в структурах данных.
    Для работы с полями timestamp with time zone преобразует все datetime
    в aware UTC.
    
    Args:
        value: Любое значение (datetime, список, словарь, etc.)
        
    Returns:
        Значение с datetime, приведёнными к aware UTC
    """
    if isinstance(value, datetime):
        return ensure_aware_utc(value)
    elif isinstance(value, list):
        return [normalize_datetime(item) for item in value]
    elif isinstance(value, dict):
        return {key: normalize_datetime(val) for key, val in value.items()}
    else:
        return value

def current_naive_utc() -> datetime:
    """Возвращает текущее время как naive datetime в UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def current_aware_utc() -> datetime:
    """Возвращает текущее время как aware datetime в UTC."""
    return datetime.now(timezone.utc)

# Алиасы для удобства
to_aware = ensure_aware_utc
to_naive = ensure_naive_utc
now_naive = current_naive_utc
now_aware = current_aware_utc