from typing import Optional
from sqlalchemy import Float, DateTime, ForeignKey, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from shared.models.base import Base

class CloseApproachModel(Base):
    """
    Модель для хранения рассчитанных сближений астероидов с Землей.
    Соответствует таблице 'close_approach_models'.
    """
    
    # Связь с астероидом
    asteroid_id: Mapped[int] = mapped_column(
        ForeignKey('asteroid_models.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Ссылка на астероид"
    )
    
    # Временные параметры сближения
    approach_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Точное время максимального сближения"
    )
    
    # Параметры сближения
    distance_au: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Расстояние в астрономических единицах"
    )
    distance_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Расстояние в километрах (рассчитанное поле)"
    )
    velocity_km_s: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Относительная скорость в км/с"
    )
    
    # NASA обозначение (для удобства, дублирует данные из asteroid)
    asteroid_designation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Обозначение NASA астероида"
    )
    asteroid_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Полное имя астероида из CAD API"
    )
    
    # Источник данных
    data_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='NASA CAD API',
        comment="Источник данных (NASA CAD API или другой)"
    )
    
    # Технические поля
    calculation_batch_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Идентификатор партии расчета (для отслеживания)"
    )
    
    # Связи
    asteroid: Mapped['AsteroidModel'] = relationship( # type: ignore
        back_populates='close_approaches',
        lazy='selectin'
    )
    
    # Уникальное ограничение
    __table_args__ = (
        UniqueConstraint('asteroid_id', 'approach_time', 
                        name='uq_asteroid_approach_time'),
        CheckConstraint(
            "distance_au >= 0",
            name='check_distance_non_negative'
        ),
        CheckConstraint(
            "velocity_km_s >= 0",
            name='check_velocity_non_negative'
        ),
    )
    
    def __init__(self, **kwargs):
        """
        Инициализирует экземпляр модели сближения с валидацией данных.
        
        Args:
            **kwargs: Параметры сближения для инициализации
        """
        super().__init__(**kwargs)
        
        # Автоматический расчет расстояния в км, если не задано
        if 'distance_km' not in kwargs and 'distance_au' in kwargs:
            self.distance_km = self.distance_au * 149597870.7
        
        # Автоматическое заполнение полей, если не заданы
        if not hasattr(self, 'asteroid_designation') or not self.asteroid_designation:
            if 'asteroid_number' in kwargs:
                self.asteroid_designation = kwargs['asteroid_number']
        
        if not hasattr(self, 'asteroid_name') or not self.asteroid_name:
            if 'asteroid_name' in kwargs:
                self.asteroid_name = kwargs['asteroid_name']
        
        if not hasattr(self, 'data_source') or not self.data_source:
            self.data_source = 'NASA CAD API'
    
    def __repr__(self) -> str:
        return f"CloseApproachModel(id={self.id}, asteroid={self.asteroid_designation}, time={self.approach_time})"