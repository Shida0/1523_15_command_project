"""
Базовый сервис для работы с моделями через UnitOfWork.
"""
from typing import Dict, Any, List, Optional, Type, Tuple
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import inspect
from decimal import Decimal
from datetime import datetime
import logging

from shared.transaction.uow import UnitOfWork
from shared.infrastructure import BaseRepository

logger = logging.getLogger(__name__)


class BaseService:
    """
    Базовый сервис для работы с одной конкретной моделью.
    Модель задается при инициализации и используется во всех методах.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], model_class: Type):
        """
        Инициализация базового сервиса.

        Args:
            session_factory: Фабрика для создания сессий SQLAlchemy
            model_class: Класс модели SQLAlchemy
        """
        self.session_factory = session_factory
        self.model_class = model_class

        logger.info(f"Инициализирован BaseService для модели {model_class.__name__}")

    # === УНИВЕРСАЛЬНЫЕ CRUD МЕТОДЫ ===

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Создание записи текущей модели.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            instance = await repo.create(data)
            return self._model_to_dict(instance) if instance else None

    async def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Получение записи по ID.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            instance = await repo.get_by_id(id)
            return self._model_to_dict(instance) if instance else None

    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """
        Получение записи по обозначению (если поддерживается).
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            if hasattr(repo, 'get_by_designation'):
                instance = await repo.get_by_designation(designation)
                return self._model_to_dict(instance) if instance else None
            else:
                # Если метод не поддерживается, используем фильтр
                instances = await self.filter({"designation": designation})
                return instances[0] if instances else None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получение всех записей с пагинацией.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            instances = await repo.get_all(skip, limit)
            return [self._model_to_dict(inst) for inst in instances]

    async def update(
        self,
        id: int,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Обновление записи.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            instance = await repo.update(id, data)
            return self._model_to_dict(instance) if instance else None

    async def delete(self, id: int) -> bool:
        """
        Удаление записи.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            return await repo.delete(id)

    async def filter(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Универсальная фильтрация записей.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            instances = await repo.filter(
                filters, skip, limit, order_by, order_desc
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
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            instances = await repo.search(
                search_term, search_fields, skip, limit
            )
            return [self._model_to_dict(inst) for inst in instances]

    async def count(self) -> int:
        """
        Подсчет общего количества записей.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            return await repo.count()

    # === МАССОВЫЕ ОПЕРАЦИИ ===

    async def bulk_create(
        self,
        data_list: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое создание записей.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            return await repo.bulk_create_asteroids(data_list) if hasattr(repo, 'bulk_create_asteroids') else await repo.bulk_create(data_list)

    async def bulk_delete(
        self,
        filters: Dict[str, Any]
    ) -> int:
        """
        Массовое удаление записей по фильтру.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            return await repo.bulk_delete(filters)

    # === СТАТИСТИЧЕСКИЕ МЕТОДЫ ===

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики для текущей модели.
        """
        async with UnitOfWork(self.session_factory) as uow:
            repo = self._get_repository(uow)
            if hasattr(repo, 'get_statistics'):
                return await repo.get_statistics()
            else:
                # Базовая статистика
                count = await self.count()
                return {
                    "total_count": count,
                    "model_type": self.model_class.__name__
                }

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _get_repository(self, uow):
        """
        Получение нужного репозитория из UnitOfWork.
        """
        if self.model_class.__name__ == "AsteroidModel":
            return uow.asteroid_repo
        elif self.model_class.__name__ == "CloseApproachModel":
            return uow.approach_repo
        elif self.model_class.__name__ == "ThreatAssessmentModel":
            return uow.threat_repo
        else:
            raise ValueError(f"Unknown model class: {self.model_class}")

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
            
            # Преобразование специальных типов
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'isoformat'):  # date objects also have isoformat
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif hasattr(value, '__dict__') and hasattr(value, '__table__'):
                # Это связанная модель, рекурсивно преобразуем
                value = self._model_to_dict(value)
            elif isinstance(value, list):
                # Это список связанных моделей
                value = [self._model_to_dict(item) for item in value]
            
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_class.__name__})"