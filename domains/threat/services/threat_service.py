"""
Сервис для работы с оценками угроз.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from domains.threat.repositories.threat_repository import ThreatRepository
from shared.transaction.uow import UnitOfWork  # Moved import to module level for testing

logger = logging.getLogger(__name__)


class ThreatService:
    """
    ⚠️ Сервис для работы с оценками угроз астероидов.
    
    Этот класс предоставляет методы для получения информации об угрозах,
    фильтрации по различным критериям угрозы и получения статистики.
    """

    def __init__(self, session_factory):
        """
        Инициализация сервиса для угроз.

        Args:
            session_factory: Фабрика для создания сессий SQLAlchemy
        """
        self.session_factory = session_factory
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ===
    
    async def get_by_designation(self, designation: str) -> Optional[Dict[str, Any]]:
        """
        🎯 Получение оценки угрозы по обозначению астероида.
        
        Args:
            designation (str): Обозначение астероида в системе NASA
            
        Returns:
            Optional[Dict[str, Any]]: Словарь с данными об оценке угрозы или None, если не найдена
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> threat = await service.get_by_designation("433")
            >>> if threat:
            >>>     print(f"Угроза для 433: Туринская шкала = {threat['ts_max']}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            threat = await uow.threat_repo.get_by_designation(designation)
            return self._model_to_dict(threat) if threat else None

    async def get_by_asteroid_id(self, asteroid_id: int) -> Optional[Dict[str, Any]]:
        """
        🔍 Получение оценки угрозы для астероида по его ID.
        
        Args:
            asteroid_id (int): Уникальный идентификатор астероида
            
        Returns:
            Optional[Dict[str, Any]]: Словарь с данными об оценке угрозы или None, если не найдена
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> threat = await service.get_by_asteroid_id(123)
            >>> if threat:
            >>>     print(f"Угроза для астероида 123: IP = {threat['ip']}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            threat = await uow.threat_repo.get_by_asteroid_id(asteroid_id)
            return self._model_to_dict(threat) if threat else None

    async def get_high_risk(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        ⚠️ Получение угроз с высоким уровнем риска (туринская шкала >= 5).
        
        Туринская шкала (Torino Scale) - это шкала от 0 до 10 для оценки риска
        столкновения астероида или кометы с Землей. Уровень 5 и выше означает
        значительную вероятность столкновения с серьезными последствиями.
        
        Args:
            limit (int): Максимальное количество возвращаемых угроз (по умолчанию 20)
            
        Returns:
            List[Dict[str, Any]]: Список угроз с высоким уровнем риска
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> high_risk = await service.get_high_risk(10)
            >>> print(f"Угрозы высокого риска: {len(high_risk)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_high_risk_threats(limit)
            return [self._model_to_dict(t) for t in threats]

    async def get_by_risk_level(
        self,
        min_ts: int = 0,
        max_ts: int = 10
    ) -> List[Dict[str, Any]]:
        """
        📊 Получение угроз по диапазону значений Туринской шкалы.
        
        Туринская шкала (Torino Scale) - это шкала от 0 до 10 для оценки риска
        столкновения астероида или кометы с Землей.
        
        Args:
            min_ts (int): Минимальное значение по Туринской шкале (по умолчанию 0)
            max_ts (int): Максимальное значение по Туринской шкале (по умолчанию 10)
            
        Returns:
            List[Dict[str, Any]]: Список угроз в заданном диапазоне значений Туринской шкалы
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> medium_risk = await service.get_by_risk_level(2, 4)
            >>> print(f"Угрозы среднего риска (2-4): {len(medium_risk)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_risk_level(min_ts, max_ts)
            return [self._model_to_dict(t) for t in threats]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        📈 Возвращает статистику по оценкам угроз астероидов.
        
        Статистика включает:
        - Общее количество оценок угроз
        - Количество угроз по уровням риска
        - Средние значения по шкалам
        - Количество угроз по категориям воздействия
        
        Returns:
            Dict[str, Any]: Словарь со статистическими данными об оценках угроз
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> stats = await service.get_statistics()
            >>> print(f"Всего оценок угроз: {stats['total_threats']}")
            >>> print(f"Угроз высокого риска: {stats['high_risk_count']}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.threat_repo.get_statistics()

    async def get_by_energy(
        self,
        min_energy: float = 0.0,
        max_energy: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        💥 Получение угроз по диапазону энергии воздействия.
        
        Энергия воздействия измеряется в мегатоннах (Mt) и представляет собой
        эквивалент энергии ядерного взрыва, который можно сравнить с воздействием
        потенциального столкновения.
        
        Args:
            min_energy (float): Минимальная энергия воздействия в мегатоннах (по умолчанию 0.0)
            max_energy (Optional[float]): Максимальная энергия воздействия в мегатоннах (по умолчанию None)
            
        Returns:
            List[Dict[str, Any]]: Список угроз в заданном диапазоне энергии воздействия
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> high_energy_threats = await service.get_by_energy(100.0, 1000.0)
            >>> print(f"Угрозы с энергией 100-1000 Мт: {len(high_energy_threats)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_energy(min_energy, max_energy)
            return [self._model_to_dict(t) for t in threats]

    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        📋 Получение угроз по категории воздействия.
        
        Категории воздействия могут включать:
        - Mercury: минимальные последствия
        - Venus: локальные последствия
        - Earth: региональные последствия
        - Mars: глобальные последствия
        - Jupiter: катастрофические последствия
        
        Args:
            category (str): Категория воздействия (например, "Mercury", "Venus", "Earth", "Mars", "Jupiter")
            
        Returns:
            List[Dict[str, Any]]: Список угроз указанной категории воздействия
            
        Example:
            >>> service = ThreatService(session_factory)
            >>> earth_threats = await service.get_by_category("Earth")
            >>> print(f"Угрозы категории Earth: {len(earth_threats)}")
        """
        from shared.transaction.uow import UnitOfWork
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_impact_category(category)
            return [self._model_to_dict(t) for t in threats]

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