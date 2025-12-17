from sqlalchemy import Float, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from .base import Base

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
        comment="Обозначение NASA астероида (дублируется для удобства запросов)"
    )
    
    # Технические поля
    calculation_batch_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment="Идентификатор партии расчета (для отслеживания)"
    )
    
    # Связи
    asteroid: Mapped['AsteroidModel'] = relationship(
        back_populates='close_approaches',
        lazy='selectin'
    )
    threat_assessment: Mapped['ThreatAssessmentModel'] = relationship(
        back_populates='close_approach',
        cascade='all, delete-orphan',
        uselist=False,
        lazy='selectin'
    )
    
    # Уникальное ограничение
    __table_args__ = (
        UniqueConstraint('asteroid_id', 'approach_time', 
                        name='uq_asteroid_approach_time'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Автоматический расчет расстояния в км, если не задано
        if 'distance_km' not in kwargs and 'distance_au' in kwargs:
            self.distance_km = self.distance_au * 149597870.7  # 1 а.е. в км
        
        # Валидация: храним только сближения ближе 1 а.е.
        if self.distance_au > 1.0:
            raise ValueError(
                f"Храним только сближения ближе 1 а.е. Получено: {self.distance_au} а.е."
            )