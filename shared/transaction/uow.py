from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional, Protocol
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import TypeVar

logger = logging.getLogger(__name__)

class AbstractRepository(ABC):
    """Abstract base class for repositories."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def add(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    async def update(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    async def delete(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[Any]:
        pass

class UnitOfWork:
    """
    Unit of Work для управления транзакциями.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self._repositories: Dict[Type[AbstractRepository], AbstractRepository] = {}

        self.asteroid_repo = None
        self.approach_repo = None
        self.threat_repo = None

    @property
    def session(self) -> AsyncSession:
        """
        Получить текущую сессию или создать новую.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork not initialized. Use as context manager or initialize manually.")
        return self._session

    def get_session(self) -> AsyncSession:
        """
        Получить текущую сессию или создать новую.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork not initialized. Use as context manager or initialize manually.")
        return self._session

    def get_repository(self, repository_cls: Type[AbstractRepository]) -> AbstractRepository:
        """
        Получить или создать экземпляр репозитория привязанный к текущей сессии.
        """
        if repository_cls not in self._repositories:
            session = self.get_session()
            repo_instance = repository_cls()
            repo_instance.session = session
            self._repositories[repository_cls] = repo_instance

        return self._repositories[repository_cls]

    async def commit(self):
        """
        Зафиксировать текущую транзакцию.
        """
        if self._session:
            try:
                await self._session.commit()
                logger.debug("Transaction committed successfully")
            except SQLAlchemyError as e:
                logger.error(f"Error committing transaction: {e}")
                await self._session.rollback()
                raise
            finally:
                self._clear_repositories()

    async def rollback(self):
        """
        Откатить текущую транзакцию.
        """
        if self._session:
            await self._session.rollback()
            logger.debug("Transaction rolled back")
            self._clear_repositories()

    def _clear_repositories(self):
        """
        Очистить кэшированные репозитории при завершении транзакции.
        """
        self._repositories.clear()

    async def __aenter__(self):
        self._session = self.session_factory()

        # Initialize the new architecture repositories
        from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
        from domains.approach.repositories.approach_repository import ApproachRepository
        from domains.threat.repositories.threat_repository import ThreatRepository

        self.asteroid_repo = AsteroidRepository()
        self.asteroid_repo.session = self._session
        self.approach_repo = ApproachRepository()
        self.approach_repo.session = self._session
        self.threat_repo = ThreatRepository()
        self.threat_repo.session = self._session

        await self._session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            if self._session:
                await self._session.close()
            self._session = None
            self._clear_repositories()