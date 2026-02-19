"""
API роутеры для Asteroid Watch.
"""
from api.asteroid_api import router as asteroid_router
from api.approach_api import router as approach_router
from api.threat_api import router as threat_router

__all__ = ["asteroid_router", "approach_router", "threat_router"]
