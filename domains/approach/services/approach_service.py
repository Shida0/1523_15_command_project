"""
Сервис для работы со сближениями.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from domains.approach.repositories.approach_repository import ApproachRepository
from shared.transaction.uow import UnitOfWork  # Moved import to module level for testing

logger = logging.getLogger(__name__)


class ApproachService:
    """
    🌍 Сервис для работы со сближениями астероидов с Землей.
    
    Этот класс предоставляет методы для получения информации о сближениях астероидов с Землей,
    фильтрации по различным критериям и получения статистики.
    """

    def __init__(self, session_factory):
        """
        Инициализация сервиса для сближений.

        Args:
            session_factory: Фабрика для создания сессий SQLAlchemy
        """
        self.session_factory = session_factory
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===
    
    async def get_upcoming(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        📅 Получение ближайших сближений астероидов с Землей.
        
        Метод возвращает сближения, отсортированные по времени (ближайшие первыми).
        
        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)
            
        Returns:
            List[Dict[str, Any]]: Список ближайших сближений
            
        Example:
            >>> service = ApproachService(session_factory)
            >>> upcoming = await service.get_upcoming(5)
            >>> print(f"Ближайшие 5 сближений: {len(upcoming)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_upcoming_approaches(limit)
            return [self._model_to_dict(a) for a in approaches]

    async def get_closest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        📏 Получение самых близких по расстоянию сближений.
        
        Метод возвращает сближения, отсортированные по расстоянию (самые близкие первыми).
        
        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)
            
        Returns:
            List[Dict[str, Any]]: Список сближений, отсортированных по расстоянию
            
        Example:
            >>> service = ApproachService(session_factory)
            >>> closest = await service.get_closest(5)
            >>> print(f"Самые близкие 5 сближений: {len(closest)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_closest_approaches_by_distance(limit)
            return [self._model_to_dict(a) for a in approaches]

    async def get_fastest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ⚡ Получение сближений с наибольшей скоростью.
        
        Метод возвращает сближения, отсортированные по скорости (самые быстрые первыми).
        
        Args:
            limit (int): Максимальное количество возвращаемых сближений (по умолчанию 10)
            
        Returns:
            List[Dict[str, Any]]: Список сближений, отсортированных по скорости
            
        Example:
            >>> service = ApproachService(session_factory)
            >>> fastest = await service.get_fastest(5)
            >>> print(f"Самые быстрые 5 сближений: {len(fastest)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_fastest_approaches(limit)
            return [self._model_to_dict(a) for a in approaches]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        📈 Возвращает статистику по сближениям астероидов с Землей.
        
        Статистика включает:
        - Общее количество сближений
        - Среднее расстояние
        - Среднюю скорость
        - Минимальное и максимальное расстояния
        - Минимальную и максимальную скорости
        
        Returns:
            Dict[str, Any]: Словарь со статистическими данными о сближениях
            
        Example:
            >>> service = ApproachService(session_factory)
            >>> stats = await service.get_statistics()
            >>> print(f"Всего сближений: {stats['total_approaches']}")
            >>> print(f"Среднее расстояние: {stats['avg_distance_au']} а.е.")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.approach_repo.get_statistics()

    async def get_by_asteroid_id(self, asteroid_id: int) -> List[Dict[str, Any]]:
        """
        🔍 Получение всех сближений для астероида по его ID.
        
        Args:
            asteroid_id (int): Уникальный идентификатор астероида
            
        Returns:
            List[Dict[str, Any]]: Список всех сближений для указанного астероида
            
        Example:
            >>> service = ApproachService(session_factory)
            >>> approaches = await service.get_by_asteroid_id(123)
            >>> print(f"Сближения для астероида 123: {len(approaches)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_by_asteroid(asteroid_id)
            return [self._model_to_dict(a) for a in approaches]

    async def get_by_asteroid_designation(self, designation: str) -> List[Dict[str, Any]]:
        """
        🔍 Получение всех сближений для астероида по его обозначению NASA.
        
        Args:
            designation (str): Обозначение астероида в системе NASA
            
        Returns:
            List[Dict[str, Any]]: Список всех сближений для астероида с указанным обозначением
            
        Example:
            >>> service = ApproachService(session_factory)
            >>> approaches = await service.get_by_asteroid_designation("433")
            >>> print(f"Сближения для астероида 433: {len(approaches)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            approaches = await uow.approach_repo.get_by_asteroid_designation(designation)
            return [self._model_to_dict(a) for a in approaches]
 
    def _model_to_dict(self, model_instance) -> Dict[str, Any]:
        """
        Преобразование экземпляра модели в словарь.
        """
        if not model_instance:
            return None

        # Проверяем, является ли это корутиной
        if hasattr(model_instance, '__await__'):
            # Если это корутина, мы не можем обработать её здесь
            # Это ошибка в логике вызова
            raise TypeError(f"Expected model instance, got coroutine: {type(model_instance)}")

        # Получаем все колонки модели
        result = {}
        try:
            for column in model_instance.__table__.columns:
                value = getattr(model_instance, column.name)
                result[column.name] = value
        except AttributeError:
            # Если у объекта нет __table__, он может быть уже словарем или другим типом
            if hasattr(model_instance, '__dict__'):
                return {k: v for k, v in model_instance.__dict__.items() if not k.startswith('_')}
            else:
                # Если это простой объект, просто возвращаем его
                return model_instance

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