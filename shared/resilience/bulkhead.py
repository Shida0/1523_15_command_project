"""
Bulkhead pattern implementation for isolating NASA API calls.
"""
import asyncio
import logging
from typing import Callable, Any, Optional
from functools import wraps
from dataclasses import dataclass
import time


logger = logging.getLogger(__name__)


@dataclass
class BulkheadConfig:
    max_concurrent_calls: int = 10
    queue_size: int = 50
    timeout: float = 30.0  # seconds


class Bulkhead:
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_calls)
        self.queue = asyncio.Queue(maxsize=config.queue_size)
        self.active_calls = 0
        self._lock = asyncio.Lock()

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        # Try to acquire a slot immediately
        if not self.semaphore.locked() or self.queue.qsize() < self.config.queue_size:
            async with self.semaphore:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.debug(f"Bulkhead execution completed for {func.__name__} in {execution_time:.2f}s")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.warning(f"Bulkhead execution failed for {func.__name__} after {execution_time:.2f}s: {e}")
                    raise
        else:
            # Queue is full, reject the call
            raise Exception(f"Bulkhead queue is full ({self.config.queue_size} items). Call to {func.__name__} rejected.")


def bulkhead(config: BulkheadConfig):
    """Decorator to apply bulkhead pattern to a function."""
    def decorator(func: Callable) -> Callable:
        bulkhead_instance = Bulkhead(config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await bulkhead_instance.execute(func, *args, **kwargs)
        
        # Attach the bulkhead instance for potential manual control
        wrapper.bulkhead = bulkhead_instance
        return wrapper
    
    return decorator


# Specific configurations for different NASA API endpoints
SBDB_BULKHEAD_CONFIG = BulkheadConfig(
    max_concurrent_calls=5,  # Limit calls to SBDB API
    queue_size=20,
    timeout=60.0
)

CAD_BULKHEAD_CONFIG = BulkheadConfig(
    max_concurrent_calls=3,  # Limit calls to CAD API
    queue_size=15,
    timeout=60.0
)

SENTRY_BULKHEAD_CONFIG = BulkheadConfig(
    max_concurrent_calls=2,  # Limit calls to Sentry API
    queue_size=10,
    timeout=120.0  # Longer timeout for Sentry API
)