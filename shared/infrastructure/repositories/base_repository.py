"""
Базовый репозиторий с общими методами для работы с базой данных.
Содержит CRUD-операции и методы фильтрации, которые наследуют все репозитории.
Включает управление транзакциями (коммиты) внутри методов.
"""
from typing import Tuple, Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
import logging
import time

from shared.models.base import Base
from shared.utils.datetime_utils import normalize_datetime

# Тип для обобщенных моделей
ModelType = TypeVar('ModelType', bound=Base)
logger = logging.getLogger(__name__)


def handle_repository_errors(default_return=None):
    """
    Декоратор для унифицированной обработки ошибок в репозиториях.
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                import os
                if os.getenv('PYTEST_CURRENT_TEST'):
                    raise
                logger.error(
                    f"Ошибка в методе {func.__name__} репозитория {self.__class__.__name__}: {e}",
                    exc_info=True
                )
                return default_return
        return wrapper
    return decorator


class BaseRepository(Generic[ModelType]):
    """Базовый класс репозитория с CRUD-операциями."""

    def __init__(self, model: Type[ModelType]):
        """Инициализация репозитория с моделью."""
        self.model = model
        self._session = None

        try:
            self._model_columns = {c.name for c in self.model.__table__.columns}
            self._model_column_types = {c.name: c.type for c in self.model.__table__.columns}
        except AttributeError:
            self._model_columns = set()
            self._model_column_types = {}

        try:
            model_name = model.__name__
        except AttributeError:
            model_name = str(model)

        logger.debug(f"Инициализирован репозиторий для модели {model_name} с кешированием")

    @property
    def session(self):
        if self._session is None:
            raise RuntimeError(
                "Repository session is not set. "
                "This repository must be used within a UnitOfWork context."
            )
        return self._session

    @session.setter
    def session(self, session: AsyncSession):
        self._session = session
    
    async def add(self, entity):
        """Add an entity to the database - UOW interface method."""
        if self.session:
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        else:
            raise ValueError("No session available for add operation")
    
    async def get(self, id):
        """Get an entity by ID - UOW interface method."""
        if self.session:
            query = select(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
            return instance
        else:
            raise ValueError("No session available for get operation")
    
    async def update(self, entity):
        """Update an entity - UOW interface method."""
        if self.session:
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        else:
            raise ValueError("No session available for update operation")
    
    async def delete(self, entity):
        """Delete an entity - UOW interface method."""
        if self.session:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        else:
            raise ValueError("No session available for delete operation")

    @property
    def _unique_fields(self):
        """Определяет уникальные поля модели (кешируется)."""
        if not hasattr(self, '_cached_unique_fields'):
            model_name = self.model.__name__
            
            if model_name == "AsteroidModel":
                self._cached_unique_fields = ["designation"]
            elif model_name == "CloseApproachModel":
                self._cached_unique_fields = ["asteroid_id", "approach_time"]
            elif model_name == "ThreatAssessmentModel":
                self._cached_unique_fields = ["asteroid_id"]  # One-to-One
            else:
                self._cached_unique_fields = []
        
        return self._cached_unique_fields

    @_unique_fields.setter
    def _unique_fields(self, value):
        """Setter for _unique_fields to support testing."""
        self._cached_unique_fields = value
    
    @handle_repository_errors(default_return=None)
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Создает новую запись в базе данных и выполняет коммит."""
        try:
            filtered_data = {k: v for k, v in data.items() if k in self._model_columns}

            if len(filtered_data) != len(data):
                extra_fields = set(data.keys()) - self._model_columns
                logger.warning(f"Extra fields ignored in create: {extra_fields}")

            instance = self.model(**filtered_data)

            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            await self.session.commit()

            logger.info(f"Создана запись {self.model.__name__} с ID {instance.id}")
            return instance

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания записи {self.model.__name__}: {e}")
            raise
    
    @handle_repository_errors(default_return=None)
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Получает запись по её ID. Без коммита (чтение)."""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance:
            logger.debug(f"Найдена запись {self.model.__name__} с ID {id}")
        else:
            logger.debug(f"Запись {self.model.__name__} с ID {id} не найдена")

        return instance

    @handle_repository_errors(default_return=None)
    async def update(
        self,
        id: int,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Обновляет запись по ID и выполняет коммит."""
        try:
            instance = await self.get_by_id(id)
            if not instance:
                logger.warning(f"Попытка обновления несуществующей записи {self.model.__name__} с ID {id}")
                return None

            for key, value in update_data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            await self.session.flush()
            await self.session.refresh(instance)
            await self.session.commit()

            logger.info(f"Обновлена запись {self.model.__name__} с ID {id}")
            return instance

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка обновления записи {self.model.__name__} с ID {id}: {e}")
            raise

    @handle_repository_errors(default_return=False)
    async def delete(self, id: int) -> bool:
        """Удаляет запись по ID и выполняет коммит."""
        try:
            instance = await self.get_by_id(id)
            if not instance:
                logger.warning(f"Попытка удаления несуществующей записи {self.model.__name__} с ID {id}")
                return False

            await self.session.delete(instance)
            await self.session.flush()
            await self.session.commit()

            logger.info(f"Удалена запись {self.model.__name__} с ID {id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка удаления записи {self.model.__name__} с ID {id}: {e}")
            raise

    @handle_repository_errors(default_return=[])
    async def get_all(
        self,
        skip: int = 0,
        limit: Optional[int] = 100
    ) -> List[ModelType]:
        """Получает все записи с пагинацией. Без коммита (чтение)."""
        query = select(self.model).offset(skip)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        instances = result.scalars().all()

        logger.debug(f"Получено {len(instances)} записей {self.model.__name__}")
        return instances

    @handle_repository_errors(default_return=0)
    async def count(self) -> int:
        """Подсчитывает общее количество записей. Без коммита (чтение)."""
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        count = result.scalar()

        logger.debug(f"Количество записей {self.model.__name__}: {count}")
        return count

    @handle_repository_errors(default_return=[])
    async def filter(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: Optional[int] = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Универсальный метод фильтрации записей. Без коммита (чтение)."""
        query = select(self.model)

        conditions = self._build_filter_conditions(filters)
        if conditions:
            query = query.where(and_(*conditions))

        if order_by:
            field = getattr(self.model, order_by, None)
            if field:
                query = query.order_by(field.desc() if order_desc else field)

        query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> list:
        """Преобразует словарь фильтров в условия SQLAlchemy."""
        conditions = []

        for key, value in filters.items():
            if "__" in key:
                field_name, operator = key.split("__", 1)
                field = getattr(self.model, field_name, None)
            else:
                field_name = key
                operator = "eq"
                field = getattr(self.model, key, None)

            if field is None:
                continue

            value = normalize_datetime(value)

            try:
                if operator == "eq":
                    condition = field == value
                elif operator == "ne":
                    condition = field != value
                elif operator == "gt":
                    condition = field > value
                elif operator == "ge":
                    condition = field >= value
                elif operator == "lt":
                    condition = field < value
                elif operator == "le":
                    condition = field <= value
                elif operator == "in":
                    condition = field.in_(value)
                elif operator == "not_in":
                    condition = field.notin_(value)
                elif operator == "like":
                    condition = field.like(f"%{value}%")
                elif operator == "ilike":
                    condition = field.ilike(f"%{value}%")
                elif operator == "is_null":
                    condition = field.is_(None)
                elif operator == "is_not_null":
                    condition = field.is_not(None)
                else:
                    continue

                if condition is not None:
                    conditions.append(condition)
            except Exception:
                continue

        return conditions
    
    async def bulk_create(
        self,
        data_list: List[Dict[str, Any]],
        conflict_action: str = "update",
        conflict_fields: Optional[List[str]] = None
    ) -> Tuple[int, int]:
        """Массовое создание записей с коммитом."""
        if not data_list:
            return 0, 0

        if not conflict_fields:
            conflict_fields = self._unique_fields

        start_time = time.time()

        try:
            if conflict_action == "update" and conflict_fields:
                return await self._bulk_create_postgresql(data_list, conflict_fields)
            else:
                return await self._bulk_create_generic(data_list, conflict_action, conflict_fields)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка массового создания записей {self.model.__name__}: {e}")
            raise
        finally:
            duration = time.time() - start_time
            logger.debug(f"Bulk create выполнен за {duration:.2f} сек для {len(data_list)} записей")

    async def _bulk_create_postgresql(
        self,
        data_list: List[Dict[str, Any]],
        conflict_fields: List[str]
    ) -> Tuple[int, int]:
        """Оптимизированная версия для PostgreSQL с ON CONFLICT DO UPDATE."""
        try:
            filtered_data_list = []
            for data in data_list:
                filtered_data = {k: v for k, v in data.items() if k in self._model_columns}
                filtered_data_list.append(filtered_data)

            stmt = pg_insert(self.model).values(filtered_data_list)

            update_dict = {}
            for column in self._model_columns:
                if column not in conflict_fields and column != 'id':
                    update_dict[column] = getattr(stmt.excluded, column)

            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_fields,
                set_=update_dict
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            total_processed = result.rowcount

            logger.info(f"PostgreSQL bulk create обработал {total_processed} записей")
            return total_processed, 0

        except Exception as e:
            await self.session.rollback()
            raise

    async def _bulk_create_generic(
        self,
        data_list: List[Dict[str, Any]],
        conflict_action: str,
        conflict_fields: List[str]
    ) -> Tuple[int, int]:
        """Универсальная версия для любых СУБД с коммитом."""
        try:
            if not conflict_fields or conflict_action not in ("update", "ignore"):
                created = 0
                for data in data_list:
                    filtered_data = {k: v for k, v in data.items() if k in self._model_columns}
                    instance = self.model(**filtered_data)
                    self.session.add(instance)
                    created += 1

                await self.session.commit()
                return created, 0

            created = 0
            updated = 0

            filtered_data_list = []
            for data in data_list:
                filtered_data = {k: v for k, v in data.items() if k in self._model_columns}
                filtered_data_list.append(filtered_data)

            for data in filtered_data_list:
                conflict_filters = {field: data.get(field) for field in conflict_fields}
                existing = await self._find_by_fields(conflict_filters)

                if existing:
                    if conflict_action == "update":
                        for key, value in data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        updated += 1
                else:
                    instance = self.model(**data)
                    self.session.add(instance)
                    created += 1

            await self.session.commit()
            logger.info(f"Bulk создание завершено. Создано: {created}, Обновлено: {updated}")
            return created, updated

        except Exception as e:
            await self.session.rollback()
            raise
    
    async def _find_by_fields(
        self,
        fields: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Ищет запись по указанным полям. Без коммита (чтение)."""
        query = select(self.model)
        conditions = []

        for field_name, value in fields.items():
            if value is not None:
                field = getattr(self.model, field_name, None)
                if field:
                    conditions.append(field == value)

        if conditions:
            query = query.where(and_(*conditions))
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        return None
    
    @handle_repository_errors(default_return=[])
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: Optional[int] = 50
    ) -> List[ModelType]:
        """Поиск по нескольким текстовым полям. Без коммита (чтение)."""
        if not search_fields:
            return []

        search_pattern = f"%{search_term}%"
        conditions = []

        for field_name in search_fields:
            field = getattr(self.model, field_name, None)
            if field and hasattr(field, "ilike"):
                conditions.append(field.ilike(search_pattern))

        if not conditions:
            return []

        query = select(self.model).where(or_(*conditions))

        query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    @handle_repository_errors(default_return=0)
    async def bulk_delete(
        self,
        filters: Dict[str, Any]
    ) -> int:
        """Массовое удаление записей по фильтру с коммитом."""
        try:
            records = await self.filter(filters, limit=None)

            deleted_count = 0
            for record in records:
                await self.session.delete(record)
                deleted_count += 1

            await self.session.commit()

            logger.info(f"Удалено {deleted_count} записей {self.model.__name__}")
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка массового удаления: {e}")
            raise
        