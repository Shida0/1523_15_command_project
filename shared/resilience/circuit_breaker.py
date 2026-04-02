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
    """Реализация паттерна Circuit Breaker для отказоустойчивости"""

    def __init__(self, config: CircuitBreakerConfig):
        """Инициализация Circuit Breaker"""
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Выполнение вызова функции через Circuit Breaker"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker transitioning to HALF_OPEN for {func.__name__}")
                else:
                    raise Exception(f"Circuit breaker is OPEN. Call to {func.__name__} blocked.")

            try:
                result = await func(*args, **kwargs)

                if self.state == CircuitState.HALF_OPEN:
                    logger.info(f"Circuit breaker reset successful for {func.__name__}")

                self._on_success()
                return result

            except self.config.expected_exception_types as e:
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
    """Декоратор для применения паттерна Circuit Breaker к функции"""
    def decorator(func: Callable) -> Callable:
        circuit_breaker_instance = CircuitBreaker(config)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit_breaker_instance.call(func, *args, **kwargs)

        wrapper.circuit_breaker = circuit_breaker_instance
        return wrapper

    return decorator


# Конфигурация для NASA API вызовов
NASA_API_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    timeout=300.0,
    recovery_timeout=60.0,
    expected_exception_types=(
        ConnectionError,
        TimeoutError,
        Exception
    )
)