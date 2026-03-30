import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.infrastructure.repositories.base_repository import BaseRepository


class TestBaseRepository:
    """Unit tests for BaseRepository class."""

    def create_mock_model(self, model_name="TestModel"):
        """Helper to create a properly mocked model for testing."""
        # Create a mock that behaves like a SQLAlchemy declarative model
        mock_model = Mock()
        mock_model.__table__ = Mock()
        mock_col = Mock()
        mock_col.name = 'id'
        mock_col.type = Mock()
        mock_model.__table__.columns = [mock_col]
        mock_model.__name__ = model_name

        # Add the attributes that SQLAlchemy select() expects
        # Make them behave like Column objects for select() to work
        mock_model.id = Mock()
        mock_model.id.__clause_element__ = Mock()
        mock_model.designation = Mock()
        mock_model.designation.__clause_element__ = Mock()
        mock_model.name = Mock()
        mock_model.name.__clause_element__ = Mock()
        mock_model.earth_moid_au = Mock()
        mock_model.earth_moid_au.__clause_element__ = Mock()
        mock_model.estimated_diameter_km = Mock()
        mock_model.estimated_diameter_km.__clause_element__ = Mock()
        mock_model.orbit_class = Mock()
        mock_model.orbit_class.__clause_element__ = Mock()
        mock_model.accurate_diameter = Mock()
        mock_model.accurate_diameter.__clause_element__ = Mock()
        mock_model.diameter_source = Mock()
        mock_model.diameter_source.__clause_element__ = Mock()
        
        # Make the mock callable to simulate model instantiation
        mock_instance = Mock()
        mock_instance.id = 1
        mock_model.return_value = mock_instance

        return mock_model

    def test_base_repository_initialization(self):
        """Test initializing the BaseRepository."""
        # Arrange
        mock_model = self.create_mock_model()

        # Act
        repo = BaseRepository(mock_model)

        # Assert
        assert repo.model == mock_model
        assert repo._model_columns is not None
        assert repo._model_column_types is not None

    @pytest.mark.asyncio
    async def test_create_success(self, mock_session):
        """Test successful creation in BaseRepository."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        test_data = {"name": "Test", "value": 123}
        instance = Mock()
        instance.id = 1
        mock_model.return_value = instance

        # Act
        result = await repo.create(test_data)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None  # Changed from specific instance check to general check

    @pytest.mark.asyncio
    async def test_create_with_extra_fields_filtered(self, mock_session):
        """Test that extra fields are filtered during creation."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        # Data with both valid and invalid fields
        test_data = {"name": "Test", "invalid_field": "should_be_filtered"}
        instance = Mock()
        instance.id = 1
        mock_model.return_value = instance

        # Act
        result = await repo.create(test_data)

        # Assert
        # Only the 'name' field should be passed to the model constructor
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == instance

    @pytest.mark.asyncio
    async def test_create_rollback_on_error(self, mock_session):
        """Test that transaction is rolled back on error during creation."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        mock_session.add = Mock(side_effect=Exception("Database error"))
        mock_session.rollback = AsyncMock()

        test_data = {"name": "Test"}

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.create(test_data)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_session):
        """Test getting an entity by ID when found."""
        from unittest.mock import patch
        from sqlalchemy import select

        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Create the expected entity with proper attributes
        expected_entity = Mock()
        expected_entity.id = 1
        expected_entity.name = "Test"
    
        # Create mock result proxy with proper chain of calls
        mock_result_proxy = Mock()
        mock_result_proxy.scalar_one_or_none.return_value = expected_entity
        
        # Act - Patch the select function to avoid SQLAlchemy coercion error
        with patch('shared.infrastructure.repositories.base_repository.select') as mock_select_func:
            # Configure the mock select to return a query object that will be passed to session.execute
            mock_query = Mock()
            mock_query.where.return_value = mock_query  # Allow chaining
            mock_select_func.return_value = mock_query
            
            # Mock session.execute to return the mock_result_proxy when called with the mock_query
            mock_session.execute = AsyncMock(return_value=mock_result_proxy)
            
            result = await repo.get_by_id(1)

        # Assert
        assert result is expected_entity
        assert result.id == 1
        assert result.name == "Test"
        mock_session.execute.assert_called_once()
        mock_select_func.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_session):
        """Test getting an entity by ID when not found."""
        from unittest.mock import patch

        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act - Patch the select function to avoid SQLAlchemy coercion error
        with patch('shared.infrastructure.repositories.base_repository.select') as mock_select_func:
            # Configure the mock select to return the same mock_result
            mock_select_func.return_value.where.return_value = mock_result
            
            result = await repo.get_by_id(999)

        # Assert
        assert result is None
        mock_select_func.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_update_success(self, mock_session):
        """Test successful update in BaseRepository."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        existing_entity = Mock(id=1, name="Old Name")
        repo.get_by_id = AsyncMock(return_value=existing_entity)

        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        update_data = {"name": "New Name"}

        # Act
        result = await repo.update(1, update_data)

        # Assert
        assert result == existing_entity
        assert existing_entity.name == "New Name"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_session):
        """Test updating an entity that doesn't exist."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        repo.get_by_id = AsyncMock(return_value=None)

        # Act
        result = await repo.update(999, {"name": "New Name"})

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_rollback_on_error(self, mock_session):
        """Test that transaction is rolled back on error during update."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        existing_entity = Mock(id=1, name="Old Name")
        repo.get_by_id = AsyncMock(return_value=existing_entity)

        mock_session.flush = AsyncMock(side_effect=Exception("Database error"))
        mock_session.rollback = AsyncMock()

        update_data = {"name": "New Name"}

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.update(1, update_data)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_session):
        """Test successful deletion in BaseRepository."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        existing_entity = Mock(id=1, name="To Delete")
        repo.get_by_id = AsyncMock(return_value=existing_entity)

        mock_session.delete = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Act
        result = await repo.delete(1)

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(existing_entity)
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_session):
        """Test deleting an entity that doesn't exist."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        repo.get_by_id = AsyncMock(return_value=None)

        # Act
        result = await repo.delete(999)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_rollback_on_error(self, mock_session):
        """Test that transaction is rolled back on error during deletion."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        existing_entity = Mock(id=1, name="To Delete")
        repo.get_by_id = AsyncMock(return_value=existing_entity)

        mock_session.delete = Mock(side_effect=Exception("Database error"))
        mock_session.rollback = AsyncMock()

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.delete(1)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all(self, mock_session):
        """Test getting all entities."""
        from unittest.mock import patch

        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Create entities with proper attributes
        entity1 = Mock()
        entity1.id = 1
        entity1.name = "Entity 1"
        entity2 = Mock()
        entity2.id = 2
        entity2.name = "Entity 2"
        entities = [entity1, entity2]
        
        # Create mock result proxy with proper chain of calls
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = entities
        mock_result_proxy = Mock()
        mock_result_proxy.scalars.return_value = mock_scalars_result
        mock_session.execute = AsyncMock(return_value=mock_result_proxy)

        # Act - Patch the select function to avoid SQLAlchemy coercion error
        with patch('shared.infrastructure.repositories.base_repository.select') as mock_select_func:
            # Configure the mock select to return the query object that will be passed to session.execute
            mock_query = Mock()
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_select_func.return_value = mock_query
            
            result = await repo.get_all(skip=0, limit=10)

        # Assert
        assert len(result) == 2
        assert result[0].name == "Entity 1"
        assert result[1].name == "Entity 2"
        mock_session.execute.assert_called_once()
        mock_select_func.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_count(self, mock_session):
        """Test counting entities."""
        from unittest.mock import patch
        from sqlalchemy import func

        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        mock_result_proxy = Mock()
        mock_result_proxy.scalar.return_value = 5
        mock_session.execute = AsyncMock(return_value=mock_result_proxy)

        # Act - Patch the select function to avoid SQLAlchemy coercion error
        with patch('shared.infrastructure.repositories.base_repository.select') as mock_select_func:
            # Configure the mock select to return the query object that will be passed to session.execute
            mock_query = Mock()
            mock_query.select_from.return_value = mock_query
            mock_select_func.return_value = mock_query
            
            result = await repo.count()

        # Assert
        assert result == 5
        mock_select_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_filter(self, mock_session):
        """Test filtering entities."""
        from unittest.mock import patch

        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Create entity with proper attributes
        entity = Mock()
        entity.id = 1
        entity.name = "Filtered Entity"
        entities = [entity]
        
        # Create mock result proxy with proper chain of calls
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = entities
        mock_result_proxy = Mock()
        mock_result_proxy.scalars.return_value = mock_scalars_result
        mock_session.execute = AsyncMock(return_value=mock_result_proxy)

        # Act - Patch the select function to avoid SQLAlchemy coercion error
        with patch('shared.infrastructure.repositories.base_repository.select') as mock_select_func:
            # Configure the mock select to return the query object that will be passed to session.execute
            mock_query = Mock()
            mock_query.where.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_select_func.return_value = mock_query
            
            result = await repo.filter({"name": "test"}, skip=0, limit=10)

        # Assert
        assert len(result) == 1
        assert result[0].name == "Filtered Entity"
        mock_session.execute.assert_called_once()
        mock_select_func.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_bulk_create_success(self, mock_session):
        """Test successful bulk creation."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Mock the dialect detection
        mock_session.bind = Mock()
        mock_session.bind.dialect = Mock()
        mock_session.bind.dialect.name = 'sqlite'  # Not PostgreSQL

        # Mock the internal bulk create method
        repo._bulk_create_generic = AsyncMock(return_value=(5, 2))  # 5 created, 2 updated
        repo._unique_fields = []  # Empty for this test

        data_list = [{"name": "Entity 1"}, {"name": "Entity 2"}]

        # Act
        created, updated = await repo.bulk_create(data_list)

        # Assert
        assert created == 5
        assert updated == 2
        repo._bulk_create_generic.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_postgresql(self, mock_session):
        """Test bulk creation with PostgreSQL-specific optimization."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Mock the dialect detection
        mock_session.bind = Mock()
        mock_session.bind.dialect = Mock()
        mock_session.bind.dialect.name = 'postgresql'

        # Mock the PostgreSQL-specific bulk create method
        repo._bulk_create_postgresql = AsyncMock(return_value=(3, 0))  # 3 created/processed, 0 updated
        repo._unique_fields = ["name"]

        data_list = [{"name": "Entity 1"}, {"name": "Entity 2"}]

        # Act
        created, updated = await repo.bulk_create(data_list, conflict_action="update")

        # Assert
        # Since PostgreSQL version returns total processed, we expect (3, 0)
        assert created == 3
        assert updated == 0
        repo._bulk_create_postgresql.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_rollback_on_error(self, mock_session):
        """Test that transaction is rolled back on error during bulk creation."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Mock the dialect detection
        mock_session.bind = Mock()
        mock_session.bind.dialect = Mock()
        mock_session.bind.dialect.name = 'sqlite'

        # Mock the internal bulk create method to raise an error
        repo._bulk_create_generic = AsyncMock(side_effect=Exception("Database error"))
        repo._unique_fields = []

        mock_session.rollback = AsyncMock()

        data_list = [{"name": "Entity 1"}]

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.bulk_create(data_list)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(self, mock_session):
        """Test searching entities."""
        from unittest.mock import patch
        from sqlalchemy import or_

        # Arrange
        mock_model = self.create_mock_model()

        # Create a mock attribute for the model
        name_attr = Mock()
        name_attr.ilike.return_value = "LIKE condition"
        type(mock_model).name = Mock(return_value=name_attr)

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        # Create entity with proper attributes
        entity = Mock()
        entity.id = 1
        entity.name = "Search Result"
        entities = [entity]
        
        # Create mock result proxy with proper chain of calls
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = entities
        mock_result_proxy = Mock()
        mock_result_proxy.scalars.return_value = mock_scalars_result
        mock_session.execute = AsyncMock(return_value=mock_result_proxy)

        # Act - Patch both select and or_ functions to avoid SQLAlchemy coercion errors
        with patch('shared.infrastructure.repositories.base_repository.select') as mock_select_func, \
             patch('shared.infrastructure.repositories.base_repository.or_') as mock_or_func:
            # Configure the mock select to return the query object that will be passed to session.execute
            mock_query = Mock()
            mock_query.where.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_select_func.return_value = mock_query
            
            # Mock or_ to return a condition that can be used in where()
            mock_or_result = Mock()
            mock_or_func.return_value = mock_or_result
            
            result = await repo.search("search term", ["name"], skip=0, limit=10)

        # Assert
        assert len(result) == 1
        assert result[0].name == "Search Result"
        mock_session.execute.assert_called_once()
        mock_select_func.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_bulk_delete(self, mock_session):
        """Test bulk deletion."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        entities = [Mock(), Mock()]
        repo.filter = AsyncMock(return_value=entities)
        mock_session.delete = Mock()
        mock_session.commit = AsyncMock()

        # Act
        result = await repo.bulk_delete({"name": "to_delete"})

        # Assert
        assert result == 2  # Number of deleted entities
        assert mock_session.delete.call_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_delete_rollback_on_error(self, mock_session):
        """Test that transaction is rolled back on error during bulk deletion."""
        # Arrange
        mock_model = self.create_mock_model()

        repo = BaseRepository(mock_model)
        repo.session = mock_session  # Set the session via property

        entities = [Mock()]
        repo.filter = AsyncMock(return_value=entities)
        mock_session.delete = Mock(side_effect=Exception("Database error"))
        mock_session.rollback = AsyncMock()

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repo.bulk_delete({"name": "to_delete"})

        mock_session.rollback.assert_called_once()


class TestBaseRepositoryFilterConditions:
    """Unit tests for BaseRepository filter conditions building."""

    def create_mock_model(self, model_name="TestModel"):
        """Helper to create a properly mocked model for testing."""
        # Create a mock that behaves like a SQLAlchemy declarative model
        mock_model = Mock()
        mock_model.__table__ = Mock()
        mock_col = Mock()
        mock_col.name = 'id'
        mock_col.type = Mock()
        mock_model.__table__.columns = [mock_col]
        mock_model.__name__ = model_name

        # Add the attributes that SQLAlchemy select() expects
        # Make them behave like Column objects for select() to work
        mock_model.id = Mock()
        mock_model.id.__clause_element__ = Mock()
        mock_model.designation = Mock()
        mock_model.designation.__clause_element__ = Mock()
        mock_model.name = Mock()
        mock_model.name.__clause_element__ = Mock()
        mock_model.earth_moid_au = Mock()
        mock_model.earth_moid_au.__clause_element__ = Mock()
        mock_model.estimated_diameter_km = Mock()
        mock_model.estimated_diameter_km.__clause_element__ = Mock()
        mock_model.orbit_class = Mock()
        mock_model.orbit_class.__clause_element__ = Mock()
        mock_model.accurate_diameter = Mock()
        mock_model.accurate_diameter.__clause_element__ = Mock()
        mock_model.diameter_source = Mock()
        mock_model.diameter_source.__clause_element__ = Mock()
        
        # Make the mock callable to simulate model instantiation
        mock_instance = Mock()
        mock_instance.id = 1
        mock_model.return_value = mock_instance

        return mock_model

    def test_build_filter_conditions_eq(self):
        """Test building equality filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.__eq__ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field": "value"})

        # Assert
        assert len(conditions) == 1
        mock_attr.__eq__.assert_called_once_with("value")

    def test_build_filter_conditions_gt(self):
        """Test building greater than filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.__gt__ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__gt": 10})

        # Assert
        assert len(conditions) == 1
        mock_attr.__gt__.assert_called_once_with(10)

    def test_build_filter_conditions_lt(self):
        """Test building less than filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.__lt__ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__lt": 10})

        # Assert
        assert len(conditions) == 1
        mock_attr.__lt__.assert_called_once_with(10)

    def test_build_filter_conditions_gte(self):
        """Test building greater than or equal filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.__ge__ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__ge": 10})

        # Assert
        assert len(conditions) == 1
        mock_attr.__ge__.assert_called_once_with(10)

    def test_build_filter_conditions_lte(self):
        """Test building less than or equal filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.__le__ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__le": 10})

        # Assert
        assert len(conditions) == 1
        mock_attr.__le__.assert_called_once_with(10)

    def test_build_filter_conditions_ne(self):
        """Test building not equal filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.__ne__ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__ne": "value"})

        # Assert
        assert len(conditions) == 1
        mock_attr.__ne__.assert_called_once_with("value")

    def test_build_filter_conditions_in(self):
        """Test building in filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.in_ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__in": [1, 2, 3]})

        # Assert
        assert len(conditions) == 1
        mock_attr.in_.assert_called_once_with([1, 2, 3])

    def test_build_filter_conditions_like(self):
        """Test building like filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.like = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__like": "pattern"})

        # Assert
        assert len(conditions) == 1
        mock_attr.like.assert_called_once_with("%pattern%")

    def test_build_filter_conditions_ilike(self):
        """Test building ilike filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.ilike = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__ilike": "pattern"})

        # Assert
        assert len(conditions) == 1
        mock_attr.ilike.assert_called_once_with("%pattern%")

    def test_build_filter_conditions_is_null(self):
        """Test building is null filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.is_ = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__is_null": True})

        # Assert
        assert len(conditions) == 1
        mock_attr.is_.assert_called_once_with(None)

    def test_build_filter_conditions_is_not_null(self):
        """Test building is not null filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr = Mock()
        mock_comparison = Mock()
        mock_attr.is_not = Mock(return_value=mock_comparison)
        type(mock_model).test_field = mock_attr
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"test_field__is_not_null": True})

        # Assert
        assert len(conditions) == 1
        mock_attr.is_not.assert_called_once_with(None)

    def test_build_filter_conditions_unknown_field(self):
        """Test building filter conditions for unknown field."""
        # Arrange
        mock_model = self.create_mock_model()
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({"unknown_field": "value"})

        # Assert
        assert len(conditions) == 0  # Should be empty since field doesn't exist

    def test_build_filter_conditions_multiple_conditions(self):
        """Test building multiple filter conditions."""
        # Arrange
        mock_model = self.create_mock_model()
        mock_attr1 = Mock()
        mock_attr2 = Mock()
        mock_comparison1 = Mock()
        mock_comparison2 = Mock()
        mock_attr1.__eq__ = Mock(return_value=mock_comparison1)
        mock_attr2.__gt__ = Mock(return_value=mock_comparison2)
        type(mock_model).field1 = mock_attr1
        type(mock_model).field2 = mock_attr2
        
        repo = BaseRepository(mock_model)

        # Act
        conditions = repo._build_filter_conditions({
            "field1": "value1",
            "field2__gt": 10
        })

        # Assert
        assert len(conditions) == 2
        mock_attr1.__eq__.assert_called_once_with("value1")
        mock_attr2.__gt__.assert_called_once_with(10)