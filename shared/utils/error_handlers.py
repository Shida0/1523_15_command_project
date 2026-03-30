# Модуль с декораторами для обработки ошибок и повторных попыток
import asyncio
import inspect
import logging
import time
from functools import wraps
from typing import Callable, Any, Optional

import aiohttp
import requests

logger = logging.getLogger(__name__)


# Стандартные настройки retry
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_MIN_WAIT = 2
DEFAULT_RETRY_MAX_WAIT = 30

# Коды ошибок HTTP для автоматического повторения
RETRY_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# NASA API rate limits
NASA_RATE_LIMIT_DELAY = 2.0
NASA_RATE_LIMIT_BURST_DELAY = 65.0


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


def retry_with_exponential_backoff(
    max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    min_wait: float = DEFAULT_RETRY_MIN_WAIT,
    max_wait: float = DEFAULT_RETRY_MAX_WAIT,
    retry_exceptions: tuple = (Exception,),
    logger: logging.Logger = logger
):
    """Декоратор для повторных попыток с экспоненциальной задержкой."""
    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
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

                        if isinstance(e, RateLimitExceededError):
                            logger.info(f"Ожидание {e.retry_after} секунд из-за rate limit")
                            await asyncio.sleep(e.retry_after)
                            continue
                        elif attempt == max_attempts:
                            break
                        elif hasattr(e, 'status_code') and e.status_code == 404:
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


def handle_nasa_api_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок NASA API."""
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

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def rate_limit_nasa_api(delay: float = NASA_RATE_LIMIT_DELAY):
    """Декоратор для соблюдения rate limits NASA API."""
    import threading
    local_storage = threading.local()

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not hasattr(local_storage, 'last_call_time'):
                    local_storage.last_call_time = 0

                current_time = time.time()
                time_since_last_call = current_time - local_storage.last_call_time

                if time_since_last_call < delay:
                    wait_time = delay - time_since_last_call
                    logger.debug(f"Соблюдение rate limit: ожидание {wait_time:.2f}с")
                    await asyncio.sleep(wait_time)

                local_storage.last_call_time = time.time()
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not hasattr(local_storage, 'last_call_time'):
                    local_storage.last_call_time = 0

                current_time = time.time()
                time_since_last_call = current_time - local_storage.last_call_time

                if time_since_last_call < delay:
                    wait_time = delay - time_since_last_call
                    logger.debug(f"Соблюдение rate limit: ожидание {wait_time:.2f}с")
                    time.sleep(wait_time)

                local_storage.last_call_time = time.time()
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """Декоратор для логирования времени выполнения функции."""
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

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_api_call(func: Callable) -> Callable:
    """Декоратор для логирования вызовов API с параметрами."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
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

        logger.info(f"API вызов: {func.__name__} с параметрами **kwargs: {safe_kwargs}")
        return func(*args, **kwargs)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def nasa_api_endpoint(max_retries: int = DEFAULT_RETRY_ATTEMPTS, rate_limit_delay: float = NASA_RATE_LIMIT_DELAY):
    """Композитный декоратор для конечных точек NASA API."""
    def decorator(func: Callable) -> Callable:
        decorated = func
        decorated = log_execution_time(decorated)
        decorated = log_api_call(decorated)
        decorated = handle_nasa_api_errors(decorated)
        decorated = rate_limit_nasa_api(rate_limit_delay)(decorated)
        decorated = retry_with_exponential_backoff(
            max_attempts=max_retries,
            min_wait=DEFAULT_RETRY_MIN_WAIT,
            max_wait=DEFAULT_RETRY_MAX_WAIT,
            retry_exceptions=(NetworkError, NASAAPIError, RateLimitExceededError)
        )(decorated)
        return decorated
    return decorator


def nasa_cad_api_endpoint(func):
    """Композитный декоратор для конечных точек NASA CAD API."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        operation_name = func.__name__
        logger.info(f"CAD API вызов: {operation_name} с параметрами: {kwargs}")
        start_time = time.time()

        try:
            result = await retry_with_exponential_backoff(
                max_attempts=3,
                min_wait=DEFAULT_RETRY_MIN_WAIT,
                max_wait=DEFAULT_RETRY_MAX_WAIT,
                retry_exceptions=(NetworkError, NASAAPIError, RateLimitExceededError, DataParseError)
            )(func)(*args, **kwargs)

            duration = time.time() - start_time

            if result is None:
                logger.warning(f"CAD API {operation_name} вернул None")
                return []
            elif isinstance(result, list) and len(result) == 0:
                logger.info(f"CAD API {operation_name}: Нет данных (пустой список)")
                return []
            elif isinstance(result, dict) and not result:
                logger.info(f"CAD API {operation_name}: Нет данных (пустой словарь)")
                return []

            logger.info(f"CAD API {operation_name} успешно выполнен за {duration:.2f}с")
            return result

        except DataParseError as e:
            duration = time.time() - start_time
            logger.error(f"Ошибка парсинга в {operation_name} после {duration:.2f}с: {e}")
            return []
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Неожиданная ошибка в {operation_name} после {duration:.2f}с: {e}")
            return []

    return wrapper


def database_operation(max_retries: int = 3, retry_exceptions: tuple = (DatabaseError,)):
    """Композитный декоратор для операций с базой данных."""
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


def validate_response(required_fields: list = None, response_validator: Callable = None):
    """Декоратор для валидации ответов API."""
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

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def fallback_on_error(fallback_value: Any = None, fallback_func: Callable = None):
    """Декоратор для возврата fallback значения при ошибке."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Ошибка в {func.__name__}, используется fallback: {type(e).__name__}: {e}")
                if fallback_func:
                    if inspect.iscoroutinefunction(fallback_func):
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

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def is_retryable_error(error: Exception) -> bool:
    """Проверяет, является ли ошибка повторяемой."""
    if isinstance(error, (NetworkError, RateLimitExceededError)):
        return True
    elif isinstance(error, NASAAPIError) and error.status_code not in {400, 401, 403, 404}:
        return True
    elif isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError, requests.exceptions.RequestException, TimeoutError)):
        return True
    return False


def should_retry_http_status(status_code: int) -> bool:
    """Проверяет, следует ли повторять запрос при данном HTTP статусе."""
    return status_code in RETRY_HTTP_STATUS_CODES


def get_retry_delay(attempt: int, base_delay: float = 2.0, max_delay: float = 60.0) -> float:
    """Рассчитывает задержку для повторной попытки."""
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)


__all__ = [
    'retry_with_exponential_backoff',
    'handle_nasa_api_errors',
    'rate_limit_nasa_api',
    'log_execution_time',
    'log_api_call',
    'nasa_api_endpoint',
    'database_operation',
    'validate_response',
    'fallback_on_error',
    'is_retryable_error',
    'should_retry_http_status',
    'get_retry_delay',
    'APIError',
    'NASAAPIError',
    'RateLimitExceededError',
    'NetworkError',
    'DataParseError',
    'DatabaseError',
]
