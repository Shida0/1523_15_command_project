from shared.infrastructure.services.update_service import UpdateService
from shared.database.engine import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

updater = UpdateService(AsyncSessionLocal)

async def main():
    await updater.update_all()
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())