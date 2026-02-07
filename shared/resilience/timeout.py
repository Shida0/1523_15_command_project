"""
Timeout handling for NASA API calls.
"""
import asyncio
import logging
from typing import Callable, Any
from functools import wraps


logger = logging.getLogger(__name__)


def timeout(seconds: float):
    """Decorator to apply timeout to a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.warning(f"Function {func.__name__} timed out after {seconds} seconds")
                raise TimeoutError(f"Call to {func.__name__} timed out after {seconds} seconds")
        
        return wrapper
    return decorator


# Default timeouts for different NASA API endpoints
NASA_API_TIMEOUTS = {
    'sbdb': 30.0,      # SBDB API timeout
    'cad': 60.0,       # CAD API timeout
    'sentry': 120.0,   # Sentry API timeout (longer for complex calculations)
    'default': 45.0    # Default timeout
}


def update_nasa_api_timeouts_from_values(nasa_api_config):
    """Update NASA API timeouts from provided configuration values."""
    global NASA_API_TIMEOUTS
    NASA_API_TIMEOUTS = {
        'sbdb': nasa_api_config.sbdb_timeout,
        'cad': nasa_api_config.cad_timeout,
        'sentry': nasa_api_config.sentry_timeout,
        'default': nasa_api_config.timeout
    }


def update_nasa_api_timeouts_from_config():
    """Update NASA API timeouts from configuration values."""
    from shared.config.config_manager import get_config
    config = get_config()
    update_nasa_api_timeouts_from_values(config.nasa_api)