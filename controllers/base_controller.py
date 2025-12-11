"""
Базовый контроллер с общими методами для работы с базой данных.
Содержит CRUD-операции и методы фильтрации, которые наследуют все контроллеры.
"""
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
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
        
