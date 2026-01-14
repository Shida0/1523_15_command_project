"""
Модуль с декораторами для обработки ошибок и повторных попыток
для всех компонентов системы Asteroid Watch.
"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, Type, Union, Optional, Dict
from datetime import datetime, timedelta

import aiohttp
import requests
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError
)

logger = logging.getLogger(__name__)

# ============================================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# ============================================================================

# Стандартные настройки retry
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_MIN_WAIT = 2
DEFAULT_RETRY_MAX_WAIT = 30

# Коды ошибок HTTP для автоматического повторения
RETRY_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# NASA API rate limits (в секундах)
NASA_RATE_LIMIT_DELAY = 2.0  # Базовая задержка между запросами
NASA_RATE_LIMIT_BURST_DELAY = 65.0  # Задержка при превышении лимита

# ============================================================================
# КЛАССЫ ИСКЛЮЧЕНИЙ
# ============================================================================

class APIError(Exception):
    """Базовое исключение для ошибок API."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(f"{message} (status: {status_code})" if status_code else message)

class NASAAPIError(APIError):
    """Ошибка при работе с NASA API."""
    pass

class RateLimitExceededError(NASAAPIError):
    """Превышен лимит запросов к NASA API."""
    def __init__(self, retry_after: int = 65):
        super().__init__("Rate limit exceeded for NASA API")
        self.retry_after = retry_after

class NetworkError(APIError):
    """Сетевая ошибка."""
    pass

class DataParseError(APIError):
    """Ошибка парсинга данных."""
    pass

class DatabaseError(Exception):
    """Ошибка базы данных."""
    pass

# ============================================================================
# ДЕКОРАТОРЫ ДЛЯ ПОВТОРНЫХ ПОПЫТОК (RETRY)
# ============================================================================

def retry_with_exponential_backoff(
    max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    min_wait: float = DEFAULT_RETRY_MIN_WAIT,
    max_wait: float = DEFAULT_RETRY_MAX_WAIT,
    retry_exceptions: tuple = (Exception,),
    logger: logging.Logger = logger
):
    """
    Декоратор для повторных попыток с экспоненциальной задержкой.
    
    Args:
        max_attempts: Максимальное количество попыток
        min_wait: Минимальная задержка в секундах
        max_wait: Максимальная задержка в секундах
        retry_exceptions: Кортеж исключений для повторения
        logger: Логгер для записи попыток
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        if attempt > 1:
                            wait_time = min(min_wait * (2 ** (attempt - 2)), max_wait)
                            logger.info(f"Попытка {attempt}/{max_attempts} для {func.__name__}, ожидание {wait_time:.1f}с")
                            await asyncio.sleep(wait_time)
                        
                        return await func(*args, **kwargs)
                    except retry_exceptions as e:
                        last_exception = e
                        logger.warning(f"Попытка {attempt}/{max_attempts} неудачна для {func.__name__}: {type(e).__name__}: {e}")
                        
                        # Проверяем, не нужно ли выбросить исключение раньше
                        if isinstance(e, RateLimitExceededError):
                            logger.info(f"Ожидание {e.retry_after} секунд из-за rate limit")
                            await asyncio.sleep(e.retry_after)
                            continue
                        elif attempt == max_attempts:
                            break
                        elif hasattr(e, 'status_code') and e.status_code == 404:
                            # 404 ошибки не повторяем
                            break
                raise last_exception or Exception(f"Все {max_attempts} попытки неудачны для {func.__name__}")
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        if attempt > 1:
                            wait_time = min(min_wait * (2 ** (attempt - 2)), max_wait)
                            logger.info(f"Попытка {attempt}/{max_attempts} для {func.__name__}, ожидание {wait_time:.1f}с")
                            time.sleep(wait_time)
                        
                        return func(*args, **kwargs)
                    except retry_exceptions as e:
                        last_exception = e
                        logger.warning(f"Попытка {attempt}/{max_attempts} неудачна для {func.__name__}: {type(e).__name__}: {e}")
                        
                        if attempt == max_attempts:
                            break
                raise last_exception or Exception(f"Все {max_attempts} попытки неудачны для {func.__name__}")
            return sync_wrapper
    return decorator

# ============================================================================
# ДЕКОРАТОРЫ ДЛЯ ОБРАБОТКИ ОШИБОК NASA API
# ============================================================================

def handle_nasa_api_errors(func: Callable) -> Callable:
    """
    Декоратор для обработки ошибок NASA API с автоматическим распознаванием
    типа ошибки и преобразованием в соответствующие исключения.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', NASA_RATE_LIMIT_BURST_DELAY))
                raise RateLimitExceededError(retry_after)
            elif e.status == 404:
                raise NASAAPIError(f"Ресурс не найден: {e.message}", e.status)
            elif e.status in RETRY_HTTP_STATUS_CODES:
                raise NetworkError(f"Ошибка сервера: {e.status}", e.status)
            else:
                raise NASAAPIError(f"Ошибка NASA API: {e.status} - {e.message}", e.status)
        except aiohttp.ClientError as e:
            raise NetworkError(f"Сетевая ошибка: {type(e).__name__}: {e}")
        except asyncio.TimeoutError:
            raise NetworkError("Таймаут при запросе к NASA API")
        except ValueError as e:
            if "JSON" in str(e):
                raise DataParseError("Ошибка парсинга JSON от NASA API")
            raise
        except Exception as e:
            # Логируем неожиданные ошибки, но пробрасываем дальше
            logger.error(f"Неожиданная ошибка в {func.__name__}: {type(e).__name__}: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', NASA_RATE_LIMIT_BURST_DELAY))
                    raise RateLimitExceededError(retry_after)
                elif e.response.status_code in RETRY_HTTP_STATUS_CODES:
                    raise NetworkError(f"Ошибка сервера: {e.response.status_code}", e.response.status_code)
                else:
                    raise NASAAPIError(f"Ошибка HTTP: {e.response.status_code}", e.response.status_code)
            elif isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                raise NetworkError(f"Сетевая ошибка: {type(e).__name__}: {e}")
            else:
                raise NetworkError(f"Ошибка запроса: {type(e).__name__}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка в {func.__name__}: {type(e).__name__}: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def rate_limit_nasa_api(delay: float = NASA_RATE_LIMIT_DELAY):
    """
    Декоратор для соблюдения rate limits NASA API.
    Добавляет задержку между вызовами функций.
    
    Args:
        delay: Задержка в секундах между вызовами
    """
    def decorator(func: Callable) -> Callable:
        last_call_time = 0
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                nonlocal last_call_time
                current_time = time.time()
                time_since_last_call = current_time - last_call_time
                
                if time_since_last_call < delay:
                    wait_time = delay - time_since_last_call
                    logger.debug(f"Соблюдение rate limit: ожидание {wait_time:.2f}с")
                    await asyncio.sleep(wait_time)
                
                last_call_time = time.time()
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                nonlocal last_call_time
                current_time = time.time()
                time_since_last_call = current_time - last_call_time
                
                if time_since_last_call < delay:
                    wait_time = delay - time_since_last_call
                    logger.debug(f"Соблюдение rate limit: ожидание {wait_time:.2f}с")
                    time.sleep(wait_time)
                
                last_call_time = time.time()
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator

# ============================================================================
# ДЕКОРАТОРЫ ДЛЯ ЛОГИРОВАНИЯ
# ============================================================================

def log_execution_time(func: Callable) -> Callable:
    """
    Декоратор для логирования времени выполнения функции.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Начало выполнения {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Завершено {func.__name__} за {execution_time:.2f}с")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Ошибка в {func.__name__} после {execution_time:.2f}с: {type(e).__name__}: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Начало выполнения {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Завершено {func.__name__} за {execution_time:.2f}с")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Ошибка в {func.__name__} после {execution_time:.2f}с: {type(e).__name__}: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def log_api_call(func: Callable) -> Callable:
    """
    Декоратор для логирования вызовов API с параметрами.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Маскируем чувствительные данные в параметрах
        safe_kwargs = {}
        for key, value in kwargs.items():
            if 'key' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                safe_kwargs[key] = '***MASKED***'
            else:
                safe_kwargs[key] = value
        
        logger.info(f"API вызов: {func.__name__} с параметрами: {safe_kwargs}")
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        safe_kwargs = {}
        for key, value in kwargs.items():
            if 'key' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                safe_kwargs[key] = '***MASKED***'
            else:
                safe_kwargs[key] = value
        
        logger.info(f"API вызов: {func.__name__} с параметрами: {safe_kwargs}")
        return func(*args, **kwargs)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# ============================================================================
# КОМПОЗИТНЫЕ ДЕКОРАТОРЫ ДЛЯ КОНКРЕТНЫХ ТИПОВ ФУНКЦИЙ
# ============================================================================

def nasa_api_endpoint(
    max_retries: int = DEFAULT_RETRY_ATTEMPTS,
    rate_limit_delay: float = NASA_RATE_LIMIT_DELAY
):
    """
    Композитный декоратор для конечных точек NASA API.
    Объединяет все необходимые обработки ошибок, retry и rate limiting.
    """
    def decorator(func: Callable) -> Callable:
        # Применяем декораторы в правильном порядке
        decorated = func
        
        # 1. Логирование времени выполнения
        decorated = log_execution_time(decorated)
        
        # 2. Логирование вызова API
        decorated = log_api_call(decorated)
        
        # 3. Обработка ошибок NASA API
        decorated = handle_nasa_api_errors(decorated)
        
        # 4. Rate limiting
        decorated = rate_limit_nasa_api(rate_limit_delay)(decorated)
        
        # 5. Retry с экспоненциальной задержкой
        decorated = retry_with_exponential_backoff(
            max_attempts=max_retries,
            min_wait=DEFAULT_RETRY_MIN_WAIT,
            max_wait=DEFAULT_RETRY_MAX_WAIT,
            retry_exceptions=(NetworkError, NASAAPIError, RateLimitExceededError)
        )(decorated)
        
        return decorated
    return decorator

def database_operation(
    max_retries: int = 3,
    retry_exceptions: tuple = (DatabaseError,)
):
    """
    Композитный декоратор для операций с базой данных.
    """
    def decorator(func: Callable) -> Callable:
        decorated = func
        decorated = log_execution_time(decorated)
        decorated = retry_with_exponential_backoff(
            max_attempts=max_retries,
            min_wait=1.0,
            max_wait=10.0,
            retry_exceptions=retry_exceptions
        )(decorated)
        return decorated
    return decorator

# ============================================================================
# ДЕКОРАТОРЫ ДЛЯ ОБРАБОТКИ РЕЗУЛЬТАТОВ
# ============================================================================

def validate_response(
    required_fields: list = None,
    response_validator: Callable = None
):
    """
    Декоратор для валидации ответов API.
    
    Args:
        required_fields: Список обязательных полей в ответе
        response_validator: Функция для кастомной валидации
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if required_fields:
                if isinstance(result, dict):
                    missing = [field for field in required_fields if field not in result]
                    if missing:
                        raise DataParseError(f"Отсутствуют обязательные поля в ответе: {missing}")
                elif isinstance(result, list) and result:
                    # Для списка проверяем первый элемент
                    if isinstance(result[0], dict):
                        missing = [field for field in required_fields if field not in result[0]]
                        if missing:
                            raise DataParseError(f"Отсутствуют обязательные поля в элементах списка: {missing}")
            
            if response_validator:
                if not response_validator(result):
                    raise DataParseError("Ответ не прошел кастомную валидацию")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if required_fields and result:
                if isinstance(result, dict):
                    missing = [field for field in required_fields if field not in result]
                    if missing:
                        raise DataParseError(f"Отсутствуют обязательные поля в ответе: {missing}")
            
            if response_validator:
                if not response_validator(result):
                    raise DataParseError("Ответ не прошел кастомную валидацию")
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

def fallback_on_error(fallback_value: Any = None, fallback_func: Callable = None):
    """
    Декоратор для возврата fallback значения при ошибке.
    
    Args:
        fallback_value: Значение для возврата при ошибке
        fallback_func: Функция для генерации fallback значения
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Ошибка в {func.__name__}, используется fallback: {type(e).__name__}: {e}")
                if fallback_func:
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    else:
                        return fallback_func(*args, **kwargs)
                return fallback_value
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Ошибка в {func.__name__}, используется fallback: {type(e).__name__}: {e}")
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                return fallback_value
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

# ============================================================================
# УТИЛИТНЫЕ ФУНКЦИИ
# ============================================================================

def is_retryable_error(error: Exception) -> bool:
    """
    Проверяет, является ли ошибка повторяемой.
    """
    if isinstance(error, (NetworkError, RateLimitExceededError)):
        return True
    elif isinstance(error, NASAAPIError) and error.status_code not in {400, 401, 403, 404}:
        return True
    elif isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError,
                          requests.exceptions.RequestException, TimeoutError)):
        return True
    return False

def should_retry_http_status(status_code: int) -> bool:
    """
    Проверяет, следует ли повторять запрос при данном HTTP статусе.
    """
    return status_code in RETRY_HTTP_STATUS_CODES

def get_retry_delay(attempt: int, base_delay: float = 2.0, max_delay: float = 60.0) -> float:
    """
    Рассчитывает задержку для повторной попытки с экспоненциальным откатом.
    """
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)

# Экспортируем все декораторы
__all__ = [
    # Основные декораторы
    'retry_with_exponential_backoff',
    'handle_nasa_api_errors',
    'rate_limit_nasa_api',
    'log_execution_time',
    'log_api_call',
    
    # Композитные декораторы
    'nasa_api_endpoint',
    'database_operation',
    
    # Декораторы для обработки результатов
    'validate_response',
    'fallback_on_error',
    
    # Утилиты
    'is_retryable_error',
    'should_retry_http_status',
    'get_retry_delay',
    
    # Исключения
    'APIError',
    'NASAAPIError',
    'RateLimitExceededError',
    'NetworkError',
    'DataParseError',
    'DatabaseError',
]