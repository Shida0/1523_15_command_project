from shared.database import async_session_factory

from domains.asteroid import AsteroidService
from domains.approach import ApproachService
from domains.threat import ThreatService


def get_asteroid_service() -> AsteroidService:
    return AsteroidService(async_session_factory)

def get_approach_service() -> ApproachService:
    return ApproachService(async_session_factory)

def get_threat_service() -> ThreatService:
    return ThreatService(async_session_factory)
