"""
Базовый контроллер с общими методами для работы с базой данных.
Содержит CRUD-операции и методы фильтрации, которые наследуют все контроллеры.
"""
from typing import Tuple, Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, update, delete, func
from sqlalchemy.sql import Select
import logging

from models.base import Base

# Тип для обобщенных моделей
ModelType = TypeVar('ModelType', bound=Base)
logger = logging.getLogger(__name__)

class BaseController(Generic[ModelType]):
    """Базовый класс контроллера с общими CRUD-операциями."""
    
    def __init__(self, model: Type[ModelType]):
        """
        Инициализирует контроллер с указанной моделью.
        
        Args:
            model: Класс модели SQLAlchemy
        """
        self.model = model
        logger.debug(f"Инициализирован контроллер для модели {model.__name__}")
    
    @property
    def _unique_fields(self):
        """Определяет уникальные поля модели."""
        # Определяем уникальные поля в зависимости от модели
        model_name = self.model.__name__
        
        if model_name == "AsteroidModel":
            return ["mpc_number"]
        elif model_name == "CloseApproachModel":
            return ["asteroid_id", "approach_time"]
        elif model_name == "ThreatAssessmentModel":
            return ["approach_id"]
        else:
            # По умолчанию пустой список
            return []
    
    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> ModelType:
        """
        Создает новую запись в базе данных.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            data: Словарь с данными для создания записи
            
        Returns:
            Созданный объект модели
            
        Raises:
            ValueError: Если данные некорректны
        """
        try:
            # Создаем экземпляр модели
            instance = self.model(**data)
            
            # Добавляем в сессию и сохраняем
            session.add(instance)
            await session.flush()  # Получаем ID без коммита
            await session.refresh(instance)  # Обновляем данные из БД
            
            logger.info(f"Создана запись {self.model.__name__} с ID {instance.id}")
            return instance
            
        except Exception as e:
            logger.error(f"Ошибка создания записи {self.model.__name__}: {e}")
            await session.rollback()
            raise
    
    async def get_by_id(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        """
        Получает запись по её ID.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            id: Идентификатор записи
            
        Returns:
            Объект модели или None, если запись не найдена
        """
        try:
            query = select(self.model).where(self.model.id == id)
            result = await session.execute(query)
            instance = result.scalar_one_or_none()
            
            if instance:
                logger.debug(f"Найдена запись {self.model.__name__} с ID {id}")
            else:
                logger.debug(f"Запись {self.model.__name__} с ID {id} не найдена")
                
            return instance
            
        except Exception as e:
            logger.error(f"Ошибка получения записи {self.model.__name__} по ID {id}: {e}")
            raise
    
    async def update(
        self, 
        session: AsyncSession, 
        id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Обновляет запись по ID.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            id: Идентификатор записи
            update_data: Словарь с данными для обновления
            
        Returns:
            Обновленный объект модели или None, если запись не найдена
        """
        try:
            # Проверяем существование записи
            instance = await self.get_by_id(session, id)
            if not instance:
                logger.warning(f"Попытка обновления несуществующей записи {self.model.__name__} с ID {id}")
                return None
            
            # Обновляем поля
            for key, value in update_data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            await session.flush()
            await session.refresh(instance)
            
            logger.info(f"Обновлена запись {self.model.__name__} с ID {id}")
            return instance
            
        except Exception as e:
            logger.error(f"Ошибка обновления записи {self.model.__name__} с ID {id}: {e}")
            await session.rollback()
            raise
    
    async def delete(self, session: AsyncSession, id: int) -> bool:
        """
        Удаляет запись по ID.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            id: Идентификатор записи
            
        Returns:
            True, если запись удалена, False если запись не найдена
        """
        try:
            # Проверяем существование записи
            instance = await self.get_by_id(session, id)
            if not instance:
                logger.warning(f"Попытка удаления несуществующей записи {self.model.__name__} с ID {id}")
                return False
            
            # Удаляем запись
            await session.delete(instance)
            await session.flush()
            
            logger.info(f"Удалена запись {self.model.__name__} с ID {id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления записи {self.model.__name__} с ID {id}: {e}")
            await session.rollback()
            raise
    
    async def get_all(
        self, 
        session: AsyncSession, 
        skip: int = 0, 
        limit: int|None = 100
    ) -> List[ModelType]:
        """
        Получает все записи с пагинацией.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список объектов модели
        """
        try:
            query = select(self.model).offset(skip).limit(limit)
            result = await session.execute(query)
            instances = result.scalars().all()
            
            logger.debug(f"Получено {len(instances)} записей {self.model.__name__}")
            return instances
            
        except Exception as e:
            logger.error(f"Ошибка получения всех записей {self.model.__name__}: {e}")
            raise
    
    async def count(self, session: AsyncSession) -> int:
        """
        Подсчитывает общее количество записей.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            
        Returns:
            Количество записей
        """
        try:
            query = select(func.count()).select_from(self.model)
            result = await session.execute(query)
            count = result.scalar()
            
            logger.debug(f"Количество записей {self.model.__name__}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Ошибка подсчета записей {self.model.__name__}: {e}")
            raise
        
    async def filter(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: Optional[int] = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Универсальный метод фильтрации записей.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            filters: Словарь условий {поле: значение}
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            order_by: Поле для сортировки
            order_desc: Сортировка по убыванию
            
        Returns:
            Отфильтрованный список записей
            
        Примеры:
            await controller.filter(session, {"is_pha": True})
            await controller.filter(session, {"diameter__gt": 100, "diameter__lt": 500})
        """
        try:
            query = select(self.model)
            
            # Применяем фильтры
            conditions = self._build_filter_conditions(filters)
            if conditions:
                query = query.where(and_(*conditions))
            
            # Применяем сортировку
            if order_by:
                field = getattr(self.model, order_by, None)
                if field:
                    query = query.order_by(field.desc() if order_desc else field)
            
            # Применяем пагинацию
            if limit:
                query = query.offset(skip).limit(limit)
            else:
                query = query.offset(skip)
            
            result = await session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка фильтрации записей {self.model.__name__}: {e}")
            raise
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> list:
        """
        Преобразует словарь фильтров в условия SQLAlchemy.
        Поддерживает расширенный синтаксис: поле__оператор
        
        Args:
            filters: Словарь условий
            
        Returns:
            Список условий SQLAlchemy
        """
        conditions = []
        
        for key, value in filters.items():
            # Поддержка операторов: field__operator
            if "__" in key:
                field_name, operator = key.split("__", 1)
                field = getattr(self.model, field_name, None)
            else:
                field_name = key
                operator = "eq"
                field = getattr(self.model, key, None)
            
            if not field:
                continue
            
            # Применяем операторы
            if operator == "eq":
                conditions.append(field == value)
            elif operator == "ne":
                conditions.append(field != value)
            elif operator == "gt":
                conditions.append(field > value)
            elif operator == "ge":
                conditions.append(field >= value)
            elif operator == "lt":
                conditions.append(field < value)
            elif operator == "le":
                conditions.append(field <= value)
            elif operator == "in":
                conditions.append(field.in_(value))
            elif operator == "not_in":
                conditions.append(field.notin_(value))
            elif operator == "like":
                conditions.append(field.like(f"%{value}%"))
            elif operator == "ilike":
                conditions.append(field.ilike(f"%{value}%"))
            elif operator == "is_null":
                conditions.append(field.is_(None))
            elif operator == "is_not_null":
                conditions.append(field.is_not(None))
        
        return conditions
    
    async def bulk_create(
        self,
        session: AsyncSession,
        data_list: List[Dict[str, Any]],
        conflict_action: str = "update",
        conflict_fields: Optional[List[str]] = None
    ) -> Tuple[int, int]:
        """
        Универсальный метод массового создания записей.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            data_list: Список словарей с данными для создания
            conflict_action: Действие при конфликте:
                - "ignore": игнорировать конфликт
                - "update": обновить существующую запись
            conflict_fields: Поля для проверки конфликта (по умолчанию уникальные поля модели)
            
        Returns:
            Кортеж (created_count, updated_count)
            
        Raises:
            ValueError: Если данные некорректны
        """
        created = 0
        updated = 0
        
        if not conflict_fields:
            conflict_fields = self._unique_fields
        
        try:
            for data in data_list:
                if conflict_fields and conflict_action in ("update", "ignore"):
                    # Проверяем существование записи по уникальным полям
                    conflict_filters = {field: data.get(field) for field in conflict_fields}
                    existing = await self._find_by_fields(session, conflict_filters)
                    
                    if existing:
                        if conflict_action == "update":
                            await self.update(session, existing.id, data)
                            updated += 1
                        # Если ignore - пропускаем создание
                        continue
                
                # Создаем новую запись
                await self.create(session, data)
                created += 1
            
            await session.commit()
            logger.info(f"Bulk создание завершено. Создано: {created}, Обновлено: {updated}")
            return created, updated
            
        except Exception as e:
            logger.error(f"Ошибка массового создания записей {self.model.__name__}: {e}")
            await session.rollback()
            raise
    
    async def _find_by_fields(
        self,
        session: AsyncSession,
        fields: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Ищет запись по указанным полям.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            fields: Словарь {поле: значение}
            
        Returns:
            Найденный объект или None
        """
        try:
            query = select(self.model)
            conditions = []
            
            for field_name, value in fields.items():
                if value is not None:
                    field = getattr(self.model, field_name, None)
                    if field:
                        conditions.append(field == value)
            
            if conditions:
                query = query.where(and_(*conditions))
                result = await session.execute(query)
                return result.scalar_one_or_none()
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска по полям: {e}")
            return None
    
    async def search(
        self,
        session: AsyncSession,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: Optional[int] = 50
    ) -> List[ModelType]:
        """
        Поиск по нескольким текстовым полям.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            search_term: Строка для поиска
            search_fields: Список полей для поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список найденных записей
        """
        try:
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
            
            if limit:
                query = query.offset(skip).limit(limit)
            else:
                query = query.offset(skip)
            
            result = await session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка поиска по термину '{search_term}': {e}")
            raise
    
    async def bulk_delete(
        self,
        session: AsyncSession,
        filters: Dict[str, Any]
    ) -> int:
        """
        Массовое удаление записей по фильтру.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            filters: Словарь условий для удаления
            
        Returns:
            Количество удаленных записей
        """
        try:
            # Находим записи для удаления
            records = await self.filter(session, filters, limit=None)
            
            # Удаляем найденные записи
            deleted_count = 0
            for record in records:
                await session.delete(record)
                deleted_count += 1
            
            await session.commit()
            logger.info(f"Удалено {deleted_count} записей {self.model.__name__}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка массового удаления: {e}")
            await session.rollback()
            raise