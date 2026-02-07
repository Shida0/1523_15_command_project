from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from shared.database.engine import AsyncSessionLocal, async_sessionmaker
from shared.transaction.uow import UnitOfWork

async_session_factory = AsyncSessionLocal

async def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_factory)

async def get_asteroid_service():
    from domains.asteroid.services.asteroid_service import AsteroidService
    return AsteroidService(async_session_factory)

async def get_approach_service():
    from domains.approach.services.approach_service import ApproachService
    return ApproachService(async_session_factory)

async def get_threat_service():
    from domains.threat.services.threat_service import ThreatService
    return ThreatService(async_session_factory)