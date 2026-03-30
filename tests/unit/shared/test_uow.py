import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from shared.transaction.uow import UnitOfWork


class TestUnitOfWork:
    """Unit tests for UnitOfWork class."""

    def test_uow_initialization(self):
        """Test initializing the UnitOfWork."""
        # Arrange
        mock_session_factory = Mock()
        
        # Act
        uow = UnitOfWork(mock_session_factory)
        
        # Assert
        assert uow.session_factory == mock_session_factory
        assert uow._session is None
        assert uow._repositories == {}

    @pytest.mark.asyncio
    async def test_uow_context_manager_flow(self, mock_session_factory):
        """Test the full context manager flow of UnitOfWork."""
        # Arrange
        mock_session = AsyncMock()
        mock_session_factory.return_value = mock_session
        mock_session.begin = AsyncMock()
        mock_session.close = AsyncMock()
        
        uow = UnitOfWork(mock_session_factory)
        
        # Act
        async with uow as active_uow:
            # During context, session should be available
            retrieved_session = active_uow.get_session()
            
        # Assert
        mock_session_factory.assert_called_once()
        mock_session.begin.assert_called_once()
        mock_session.close.assert_called_once()
        assert retrieved_session == mock_session
        assert active_uow._session is None  # Should be cleared after exit

    @pytest.mark.asyncio
    async def test_uow_commit_success(self, mock_session_factory):
        """Test successful commit in UnitOfWork."""
        # Arrange
        mock_session = AsyncMock()
        mock_session_factory.return_value = mock_session
        mock_session.begin = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        uow = UnitOfWork(mock_session_factory)
        
        # Act
        async with uow as active_uow:
            # Simulate some work
            pass
        
        # Assert
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_uow_rollback_on_exception(self, mock_session_factory):
        """Test rollback when exception occurs in UnitOfWork."""
        # Arrange
        mock_session = AsyncMock()
        mock_session_factory.return_value = mock_session
        mock_session.begin = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        
        uow = UnitOfWork(mock_session_factory)
        
        # Act & Assert
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test exception")
        
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_get_session_when_not_initialized(self):
        """Test getting session when UnitOfWork is not initialized."""
        # Arrange
        mock_session_factory = Mock()
        uow = UnitOfWork(mock_session_factory)
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="UnitOfWork not initialized"):
            uow.get_session()

    @pytest.mark.asyncio
    async def test_get_repository_caching(self, mock_session_factory):
        """Test that repositories are cached in UnitOfWork."""
        # Arrange
        from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
        
        mock_session = AsyncMock()
        mock_session_factory.return_value = mock_session
        mock_session.begin = AsyncMock()
        mock_session.close = AsyncMock()
        
        uow = UnitOfWork(mock_session_factory)
        
        # Act
        async with uow as active_uow:
            repo1 = active_uow.get_repository(AsteroidRepository)
            repo2 = active_uow.get_repository(AsteroidRepository)
        
        # Assert
        assert repo1 is repo2  # Same instance due to caching
        assert isinstance(repo1, AsteroidRepository)
        assert repo1.session == mock_session

    @pytest.mark.asyncio
    async def test_uow_properties_initialization(self, mock_session_factory):
        """Test that UoW initializes repository properties correctly."""
        # Arrange
        mock_session = AsyncMock()
        mock_session_factory.return_value = mock_session
        mock_session.begin = AsyncMock()
        mock_session.close = AsyncMock()
        
        uow = UnitOfWork(mock_session_factory)
        
        # Act
        async with uow as active_uow:
            # Properties should be initialized
            asteroid_repo = active_uow.asteroid_repo
            approach_repo = active_uow.approach_repo
            threat_repo = active_uow.threat_repo
        
        # Assert
        from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
        from domains.approach.repositories.approach_repository import ApproachRepository
        from domains.threat.repositories.threat_repository import ThreatRepository
        
        assert isinstance(asteroid_repo, AsteroidRepository)
        assert isinstance(approach_repo, ApproachRepository)
        assert isinstance(threat_repo, ThreatRepository)
        assert asteroid_repo.session == mock_session
        assert approach_repo.session == mock_session
        assert threat_repo.session == mock_session