"""
Базовый сервис для работы с моделями через контроллеры.
"""
from typing import Dict, Any, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from controllers.base_controller import BaseController

logger = logging.getLogger(__name__)


class BaseService:
    """
    Базовый сервис для работы с одной конкретной моделью.
    Модель задается при инициализации и используется во всех методах.
    """
    
    def __init__(self, session: AsyncSession, controller: BaseController):
        """
        Инициализация базового сервиса.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            controller: Контроллер для работы с моделью
        """
        self.session = session
        self.controller = controller
        
        logger.info(f"Инициализирован BaseService с контроллером {controller.__class__.__name__}")
    
    # === УНИВЕРСАЛЬНЫЕ CRUD МЕТОДЫ ===
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание записи текущей модели.
        """
        instance = await self.controller.create(self.session, data)
        return self._model_to_dict(instance)
    
    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Получение записи по ID.
        """
        instance = await self.controller.get_by_id(self.session, id)
        return self._model_to_dict(instance) if instance else None
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int|None = 100
    ) -> List[Dict[str, Any]]:
        """
        Получение всех записей с пагинацией.
        """
        instances = await self.controller.get_all(self.session, skip, limit)
        return [self._model_to_dict(inst) for inst in instances]
    
    async def update(
        self, 
        id: int, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Обновление записи.
        """
        instance = await self.controller.update(self.session, id, data)
        return self._model_to_dict(instance) if instance else None
    
    async def delete(self, id: int) -> bool:
        """
        Удаление записи.
        """
        return await self.controller.delete(self.session, id)
    
    async def filter(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Универсальная фильтрация записей.
        """
        instances = await self.controller.filter(
            self.session, filters, skip, limit, order_by, order_desc
        )
        return [self._model_to_dict(inst) for inst in instances]
    
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Поиск по текстовым полям.
        """
        instances = await self.controller.search(
            self.session, search_term, search_fields, skip, limit
        )
        return [self._model_to_dict(inst) for inst in instances]
    
    async def count(self) -> int:
        """
        Подсчет общего количества записей.
        """
        return await self.controller.count(self.session)
    
    # === СТАТИСТИЧЕСКИЕ МЕТОДЫ ===
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики для текущей модели.
        """
        if hasattr(self.controller, 'get_statistics'):
            return await self.controller.get_statistics(self.session)
        else:
            # Базовая статистика
            count = await self.count()
            return {
                "total_count": count,
                "controller_type": self.controller.__class__.__name__
            }
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _model_to_dict(self, model_instance) -> Dict[str, Any]:
        """
        Преобразование экземпляра модели в словарь.
        """
        if not model_instance:
            return None
        
        # Получаем все колонки модели
        result = {}
        for column in model_instance.__table__.columns:
            value = getattr(model_instance, column.name)
            result[column.name] = value
        
        # Добавляем связанные данные если они загружены
        if hasattr(model_instance, '__dict__'):
            for key, value in model_instance.__dict__.items():
                if not key.startswith('_') and key not in result:
                    # Обрабатываем отношения
                    if hasattr(value, '__table__'):  # Это другая модель
                        result[key] = self._model_to_dict(value)
                    elif isinstance(value, list):  # Список моделей
                        result[key] = [self._model_to_dict(item) for item in value]
                    else:
                        result[key] = value
        
        return result
    
    async def close(self):
        """Закрытие сессии (если требуется)."""
        await self.session.close()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"