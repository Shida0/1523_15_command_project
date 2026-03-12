import asyncio
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict
from functools import wraps
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    timeout: float = 60.0  # seconds
    recovery_timeout: float = 30.0  # seconds
    expected_exception_types: tuple = (Exception,)


class CircuitBreaker:
    """
    🛡️ Реализация паттерна Circuit Breaker для обеспечения отказоустойчивости.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        """
        Инициализирует Circuit Breaker с заданной конфигурацией.
        
        Args:
            config (CircuitBreakerConfig): Конфигурация Circuit Breaker
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        📞 Выполнить вызов функции через Circuit Breaker.
        
        Args:
            func (Callable): Функция для вызова
            *args: Позиционные аргументы для функции
            **kwargs: Именованные аргументы для функции
            
        Returns:
            Any: Результат выполнения функции
            
        Raises:
            Exception: Если Circuit Breaker открыт и вызов заблокирован
                        или если функция завершается с ошибкой
            
        Example:
            >>> async def risky_function():
            ...     # Некоторая функция, которая может завершиться неудачей
            ...     pass
            >>> 
            >>> circuit_breaker = CircuitBreaker(NASA_API_CIRCUIT_CONFIG)
            >>> try:
            ...     result = await circuit_breaker.call(risky_function)
            ... except Exception as e:
            ...     print(f"Вызов заблокирован: {e}")
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker transitioning to HALF_OPEN for {func.__name__}")
                else:
                    raise Exception(f"Circuit breaker is OPEN. Call to {func.__name__} blocked.")

            try:
                result = await func(*args, **kwargs)

                # Success case
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(f"Circuit breaker reset successful for {func.__name__}")

                self._on_success()
                return result

            except self.config.expected_exception_types as e:
                # Failure case
                self._on_failure()
                logger.warning(f"Circuit breaker detected failure for {func.__name__}: {e}")
                raise

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    def _on_success(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} consecutive failures")


def circuit_breaker(config: CircuitBreakerConfig):
    """
    🎨 Декоратор для применения паттерна Circuit Breaker к функции.
    
    Args:
        config (CircuitBreakerConfig): Конфигурация Circuit Breaker
        
    Returns:
        Callable: Декоратор для оборачивания функций
        
    Example:
        >>> @circuit_breaker(NASA_API_CIRCUIT_CONFIG)
        ... async def fetch_nasa_data():
        ...     # Код для получения данных от NASA API
        ...     pass
        >>> 
        >>> # Теперь вызовы функции будут проходить через Circuit Breaker
        >>> result = await fetch_nasa_data()
    """
    def decorator(func: Callable) -> Callable:
        circuit_breaker_instance = CircuitBreaker(config)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit_breaker_instance.call(func, *args, **kwargs)

        # Attach the circuit breaker instance for potential manual control
        wrapper.circuit_breaker = circuit_breaker_instance
        return wrapper

    return decorator


# Specific configuration for NASA API calls
NASA_API_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    timeout=300.0,  # 5 minutes timeout
    recovery_timeout=60.0,  # 1 minute before attempting reset
    expected_exception_types=(
        ConnectionError, 
        TimeoutError, 
        Exception  # More generic for API-specific exceptions
    )
)