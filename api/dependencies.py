from typing import Generator
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from shared.database.engine import AsyncSessionLocal, async_sessionmaker
from shared.transaction.uow import UnitOfWork

from domains.asteroid.services.asteroid_service import AsteroidService
from domains.approach.services.approach_service import ApproachService
from domains.threat.services.threat_service import ThreatService

async_session_factory = AsyncSessionLocal

async def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_factory)

def get_asteroid_service() -> AsteroidService:
    return AsteroidService(async_session_factory)

def get_approach_service() -> ApproachService:
    return ApproachService(async_session_factory)

def get_threat_service() -> ThreatService:
    return ThreatService(async_session_factory)