"""
Базовый сервис с общими методами для всех сервисов.
Содержит методы преобразования данных и общие утилиты.
"""
from typing import Type, TypeVar, Generic, Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from models.base import Base
from controllers.base_controller import BaseController

# Типы для обобщений
ModelType = TypeVar('ModelType', bound=Base)
SchemaType = TypeVar('SchemaType', bound=BaseModel)
ControllerType = TypeVar('ControllerType', bound=BaseController)

logger = logging.getLogger(__name__)


class BaseService:
    """Базовый класс для всех сервисов."""
    
    def __init__(self):
        """Инициализирует базовый сервис."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def model_to_dict(model_instance: Base, exclude: List[str] = None) -> Dict[str, Any]:
        """
        Преобразует модель SQLAlchemy в словарь.
        
        Args:
            model_instance: Экземпляр модели SQLAlchemy
            exclude: Список полей для исключения
            
        Returns:
            Словарь с данными модели
        """
        if not model_instance:
            return {}
        
        result = {}
        exclude_set = set(exclude or [])
        
        for column in model_instance.__table__.columns:
            column_name = column.name
            if column_name not in exclude_set:
                result[column_name] = getattr(model_instance, column_name)
        
        return result
    
    @staticmethod
    def model_to_pydantic(model_instance: Base, schema_class: Type[SchemaType]) -> SchemaType:
        """
        Преобразует модель SQLAlchemy в Pydantic схему.
        
        Args:
            model_instance: Экземпляр модели SQLAlchemy
            schema_class: Класс Pydantic схемы
            
        Returns:
            Экземпляр Pydantic схемы
            
        Raises:
            ValueError: Если модель или схема не указаны
        """
        if not model_instance:
            raise ValueError("Модель не может быть None")
        
        if not schema_class:
            raise ValueError("Класс схемы не может быть None")
        
        try:
            # Преобразуем модель в словарь
            model_dict = BaseService.model_to_dict(model_instance)
            
            # Создаем Pydantic объект из словаря
            return schema_class(**model_dict)
            
        except Exception as e:
            logger.error(f"Ошибка преобразования модели в Pydantic: {e}")
            raise
    
    @staticmethod
    def models_to_pydantic_list(
        model_list: List[Base], 
        schema_class: Type[SchemaType]
    ) -> List[SchemaType]:
        """
        Преобразует список моделей SQLAlchemy в список Pydantic схем.
        
        Args:
            model_list: Список экземпляров моделей SQLAlchemy
            schema_class: Класс Pydantic схемы
            
        Returns:
            Список экземпляров Pydantic схем
        """
        if not model_list:
            return []
        
        return [BaseService.model_to_pydantic(model, schema_class) for model in model_list]
    
    @staticmethod
    def dict_to_pydantic(data_dict: Dict[str, Any], schema_class: Type[SchemaType]) -> SchemaType:
        """
        Преобразует словарь в Pydantic схему.
        
        Args:
            data_dict: Словарь с данными
            schema_class: Класс Pydantic схемы
            
        Returns:
            Экземпляр Pydantic схемы
        """
        if not data_dict:
            raise ValueError("Словарь данных не может быть пустым")
        
        try:
            return schema_class(**data_dict)
        except Exception as e:
            logger.error(f"Ошибка преобразования словаря в Pydantic: {e}")
            raise
    
    @staticmethod
    def merge_dicts(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Объединяет два словаря, приоритет у update_dict.
        
        Args:
            base_dict: Базовый словарь
            update_dict: Словарь с обновлениями
            
        Returns:
            Объединенный словарь
        """
        result = base_dict.copy()
        result.update(update_dict)
        return result
    
    @staticmethod
    def filter_dict_by_keys(data_dict: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """
        Фильтрует словарь, оставляя только указанные ключи.
        
        Args:
            data_dict: Исходный словарь
            keys: Список ключей для сохранения
            
        Returns:
            Отфильтрованный словарь
        """
        if not keys:
            return data_dict
        
        return {k: v for k, v in data_dict.items() if k in keys}
    
    def log_service_call(self, method_name: str, **kwargs):
        """
        Логирует вызов метода сервиса.
        
        Args:
            method_name: Имя вызываемого метода
            **kwargs: Аргументы метода
        """
        self.logger.debug(f"Вызов метода {method_name} с параметрами: {kwargs}")
    
    def log_service_result(self, method_name: str, result: Any):
        """
        Логирует результат вызова метода сервиса.
        
        Args:
            method_name: Имя вызванного метода
            result: Результат выполнения
        """
        result_str = f"тип: {type(result).__name__}"
        
        if isinstance(result, list):
            result_str += f", количество: {len(result)}"
        elif isinstance(result, dict):
            result_str += f", ключи: {list(result.keys())}"
        
        self.logger.debug(f"Метод {method_name} завершен. Результат: {result_str}")
    
    async def handle_service_error(
        self, 
        method_name: str, 
        error: Exception, 
        session: AsyncSession = None
    ):
        """
        Обрабатывает ошибки в сервисах.
        
        Args:
            method_name: Имя метода, в котором произошла ошибка
            error: Исключение
            session: Сессия БД (для отката)
        """
        self.logger.error(f"Ошибка в методе {method_name}: {error}")
        
        if session:
            try:
                await session.rollback()
                self.logger.debug(f"Откат транзакции после ошибки в {method_name}")
            except Exception as rollback_error:
                self.logger.error(f"Ошибка при откате транзакции: {rollback_error}")
        
        raise error


class ServiceWithController(BaseService, Generic[ControllerType]):
    """Базовый сервис с привязанным контроллером."""
    
    def __init__(self, controller: ControllerType):
        """
        Инициализирует сервис с контроллером.
        
        Args:
            controller: Контроллер для работы с БД
        """
        super().__init__()
        self.controller = controller
    
    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> Any:
        """
        Создает запись через контроллер.
        
        Args:
            session: Сессия БД
            data: Данные для создания
            
        Returns:
            Созданный объект
        """
        self.log_service_call("create", data=data)
        
        try:
            result = await self.controller.create(session, data)
            self.log_service_result("create", result)
            return result
        except Exception as e:
            await self.handle_service_error("create", e, session)
    
    async def get_by_id(self, session: AsyncSession, id: int) -> Optional[Any]:
        """
        Получает запись по ID через контроллер.
        
        Args:
            session: Сессия БД
            id: ID записи
            
        Returns:
            Объект или None
        """
        self.log_service_call("get_by_id", id=id)
        
        try:
            result = await self.controller.get_by_id(session, id)
            self.log_service_result("get_by_id", result)
            return result
        except Exception as e:
            await self.handle_service_error("get_by_id", e, session)
            return None
    
    async def update(
        self, 
        session: AsyncSession, 
        id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Обновляет запись через контроллер.
        
        Args:
            session: Сессия БД
            id: ID записи
            update_data: Данные для обновления
            
        Returns:
            Обновленный объект или None
        """
        self.log_service_call("update", id=id, update_data=update_data)
        
        try:
            result = await self.controller.update(session, id, update_data)
            self.log_service_result("update", result)
            return result
        except Exception as e:
            await self.handle_service_error("update", e, session)
            return None
    
    async def delete(self, session: AsyncSession, id: int) -> bool:
        """
        Удаляет запись через контроллер.
        
        Args:
            session: Сессия БД
            id: ID записи
            
        Returns:
            True если удалено, иначе False
        """
        self.log_service_call("delete", id=id)
        
        try:
            result = await self.controller.delete(session, id)
            self.log_service_result("delete", result)
            return result
        except Exception as e:
            await self.handle_service_error("delete", e, session)
            return False
    
    async def get_all(
        self, 
        session: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Any]:
        """
        Получает все записи через контроллер.
        
        Args:
            session: Сессия БД
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список объектов
        """
        self.log_service_call("get_all", skip=skip, limit=limit)
        
        try:
            result = await self.controller.get_all(session, skip, limit)
            self.log_service_result("get_all", result)
            return result
        except Exception as e:
            await self.handle_service_error("get_all", e, session)
            return []
    
    async def count(self, session: AsyncSession) -> int:
        """
        Подсчитывает количество записей через контроллер.
        
        Args:
            session: Сессия БД
            
        Returns:
            Количество записей
        """
        self.log_service_call("count")
        
        try:
            result = await self.controller.count(session)
            self.log_service_result("count", result)
            return result
        except Exception as e:
            await self.handle_service_error("count", e, session)
            return 0