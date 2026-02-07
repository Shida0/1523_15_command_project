"""
Transactional service for Asteroid entities using Unit of Work pattern.
"""
from typing import Optional, List, Dict, Any
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal
from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
from domains.asteroid.models.asteroid import AsteroidModel


class TransactionalAsteroidService:
    """Service for managing asteroids with transactional operations."""
    
    @staticmethod
    async def create_asteroid(asteroid_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new asteroid within a transaction."""
        async with UnitOfWork(AsyncSessionLocal) as uow:
            asteroid = AsteroidModel(**asteroid_data)
            uow.session.add(asteroid)
            await uow.commit()
            return uow.asteroid_repo._model_to_dict(asteroid) if asteroid else None
    
    @staticmethod
    async def update_asteroid(asteroid_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an asteroid within a transaction."""
        async with UnitOfWork(AsyncSessionLocal) as uow:
            existing_asteroid = await uow.asteroid_repo.get_by_id(asteroid_id)
            if not existing_asteroid:
                return None
            
            # Update the asteroid attributes
            for key, value in update_data.items():
                setattr(existing_asteroid, key, value)
            
            await uow.commit()
            return uow.asteroid_repo._model_to_dict(existing_asteroid) if existing_asteroid else None
    
    @staticmethod
    async def delete_asteroid(asteroid_id: int) -> bool:
        """Delete an asteroid within a transaction."""
        async with UnitOfWork(AsyncSessionLocal) as uow:
            asteroid = await uow.asteroid_repo.get_by_id(asteroid_id)
            if not asteroid:
                return False
            
            await uow.session.delete(asteroid)
            await uow.commit()
            return True
    
    @staticmethod
    async def get_asteroid_by_id(asteroid_id: int) -> Optional[Dict[str, Any]]:
        """Get an asteroid by ID within a transaction."""
        async with UnitOfWork(AsyncSessionLocal) as uow:
            asteroid = await uow.asteroid_repo.get_by_id(asteroid_id)
            return uow.asteroid_repo._model_to_dict(asteroid) if asteroid else None
    
    @staticmethod
    async def get_asteroid_by_designation(designation: str) -> Optional[Dict[str, Any]]:
        """Get an asteroid by designation within a transaction."""
        async with UnitOfWork(AsyncSessionLocal) as uow:
            asteroid = await uow.asteroid_repo.get_by_designation(designation)
            return uow.asteroid_repo._model_to_dict(asteroid) if asteroid else None
    
    @staticmethod
    async def get_all_asteroids(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all asteroids within a transaction."""
        async with UnitOfWork(AsyncSessionLocal) as uow:
            asteroids = await uow.asteroid_repo.get_all(skip, limit)
            return [uow.asteroid_repo._model_to_dict(asteroid) for asteroid in asteroids]
    
    @staticmethod
    async def complex_asteroid_operation(asteroids_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform a complex operation involving multiple asteroids within a single transaction.
        If any operation fails, all changes are rolled back.
        """
        async with UnitOfWork(AsyncSessionLocal) as uow:
            results = []
            
            for asteroid_data in asteroids_data:
                # Attempt to create each asteroid
                asteroid = AsteroidModel(**asteroid_data)
                uow.session.add(asteroid)
                await uow.session.flush()  # Get the ID without committing
                results.append(uow.asteroid_repo._model_to_dict(asteroid))
            
            # Commit all changes at once
            await uow.commit()
            return results