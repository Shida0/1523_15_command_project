"""
Сервис для работы с оценками угроз.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from shared.infrastructure.services.base_service import BaseService
from domains.threat.models.threat_assessment import ThreatAssessmentModel
from shared.transaction.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ThreatService(BaseService):
    """
    Сервис для работы с оценками угроз астероидов.
    Наследуется от BaseService для общих CRUD операций.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, ThreatAssessmentModel)

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
        async with UnitOfWork(self.session_factory) as uow:
            threat = await uow.threat_repo.get_by_asteroid_id(asteroid_id)
            return self._model_to_dict(threat) if threat else None

    async def get_high_risk(self, limit: Optional[int] = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        ⚠️ Получение угроз с высоким уровнем риска (туринская шкала >= 5).
        Туринская шкала (Torino Scale) - это шкала от 0 до 10 для оценки риска
        столкновения астероида или кометы с Землей. Уровень 5 и выше означает
        значительную вероятность столкновения с серьезными последствиями.

        Args:
            limit (int): Максимальное количество возвращаемых угроз (по умолчанию 20)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)

        Returns:
            List[Dict[str, Any]]: Список угроз с высоким уровнем риска

        Example:
            >>> service = ThreatService(session_factory)
            >>> high_risk = await service.get_high_risk(10)
            >>> print(f"Угрозы высокого риска: {len(high_risk)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_high_risk_threats(limit=limit, skip=skip)
            return [self._model_to_dict(t) for t in threats]

    async def get_by_risk_level(
        self,
        min_ts: int = 0,
        max_ts: int = 10,
        skip: int = 0,
        limit: Optional[int] = 100
    ) -> List[Dict[str, Any]]:
        """
        📊 Получение угроз по диапазону значений Туринской шкалы.
        Туринская шкала (Torino Scale) - это шкала от 0 до 10 для оценки риска
        столкновения астероида или кометы с Землей.

        Args:
            min_ts (int): Минимальное значение по Туринской шкале (по умолчанию 0)
            max_ts (int): Максимальное значение по Туринской шкале (по умолчанию 10)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список угроз в заданном диапазоне значений Туринской шкалы

        Example:
            >>> service = ThreatService(session_factory)
            >>> medium_risk = await service.get_by_risk_level(2, 4)
            >>> print(f"Угрозы среднего риска (2-4): {len(medium_risk)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_risk_level(
                min_ts, max_ts, skip=skip, limit=limit
            )
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
        async with UnitOfWork(self.session_factory) as uow:
            return await uow.threat_repo.get_statistics()

    async def get_by_probability(
        self,
        min_probability: float = 0.0,
        max_probability: float = 1.0,
        skip: int = 0,
        limit: Optional[int] = 100
    ) -> List[Dict[str, Any]]:
        """
        🎯 Получение угроз по диапазону вероятности столкновения.
        Вероятность столкновения (impact probability) - это вероятность того,
        что астероид столкнется с Землей в определенный момент времени.

        Args:
            min_probability (float): Минимальная вероятность столкновения (по умолчанию 0.0)
            max_probability (float): Максимальная вероятность столкновения (по умолчанию 1.0)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список угроз в заданном диапазоне вероятности столкновения

        Example:
            >>> service = ThreatService(session_factory)
            >>> probable_threats = await service.get_by_probability(0.001, 0.01)
            >>> print(f"Угрозы с вероятностью 0.1%-1%: {len(probable_threats)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_probability(
                min_probability, max_probability, skip=skip, limit=limit
            )
            return [self._model_to_dict(t) for t in threats]

    async def get_by_energy(
        self,
        min_energy: float = 0.0,
        max_energy: Optional[float] = None,
        skip: int = 0,
        limit: Optional[int] = 100
    ) -> List[Dict[str, Any]]:
        """
        💥 Получение угроз по диапазону энергии воздействия.
        Энергия воздействия измеряется в мегатоннах (Mt) и представляет собой
        эквивалент энергии ядерного взрыва.

        Args:
            min_energy (float): Минимальная энергия воздействия в мегатоннах (по умолчанию 0.0)
            max_energy (Optional[float]): Максимальная энергия воздействия в мегатоннах (по умолчанию None)
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список угроз в заданном диапазоне энергии воздействия

        Example:
            >>> service = ThreatService(session_factory)
            >>> high_energy_threats = await service.get_by_energy(100.0, 1000.0)
            >>> print(f"Угрозы с энергией 100-1000 Мт: {len(high_energy_threats)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_energy(
                min_energy, max_energy, skip=skip, limit=limit
            )
            return [self._model_to_dict(t) for t in threats]

    async def get_by_category(self, category: str, skip: int = 0, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """
        📋 Получение угроз по категории воздействия.
        Категории: локальный, региональный, глобальный

        Args:
            category (str): Категория воздействия 
            skip (int): Количество пропускаемых записей (для пагинации, по умолчанию 0)
            limit (int): Максимальное количество возвращаемых записей (по умолчанию 100)

        Returns:
            List[Dict[str, Any]]: Список угроз указанной категории воздействия

        Example:
            >>> service = ThreatService(session_factory)
            >>> earth_threats = await service.get_by_category("Earth")
            >>> print(f"Угрозы категории Earth: {len(earth_threats)}")
        """
        async with UnitOfWork(self.session_factory) as uow:
            threats = await uow.threat_repo.get_threats_by_impact_category(
                category, skip=skip, limit=limit
            )
            return [self._model_to_dict(t) for t in threats]
