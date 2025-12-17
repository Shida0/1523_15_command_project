from sqlalchemy import CheckConstraint, Float, String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from .base import Base

class AsteroidModel(Base):
    """
    Модель для хранения данных о потенциально опасных астероидах (PHA).
    Соответствует таблице 'asteroid_models' (автоматически из Base).
    """
    
    # Основные идентификаторы NASA
    designation: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Обозначение NASA (напр., '99942', '2025 XN4') - первичный идентификатор"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Собственное название астероида (напр., 'Apophis')"
    )
    
    # Орбитальные параметры (могут отсутствовать в данных NASA)
    perihelion_au: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Расстояние перигелия в астрономических единицах (может быть NULL)"
    )
    aphelion_au: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Расстояние афелия в астрономических единицах (может быть NULL)"
    )
    earth_moid_au: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Минимальное расстояние пересечения орбит с Землей (MOID)"
    )
    
    # Физические характеристики
    absolute_magnitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Абсолютная звездная величина (H)"
    )
    estimated_diameter_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Расчетный диаметр в километрах"
    )
    accurate_diameter: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Диаметр точный или же расчитан нами по стандартному альбедо"
    )
    albedo: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Альбедо (отражательная способность), если известно"
    )
    
    # Дополнительные данные NASA
    orbit_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="ID орбиты из NASA SBDB"
    )
    orbit_class: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Класс орбиты (напр., 'Apollo', 'Aten', 'Amor')"
    )
    
    # Связи с другими таблицами
    close_approaches: Mapped[List['CloseApproachModel']] = relationship(
        back_populates='asteroid',
        cascade='all, delete-orphan',
        lazy='selectin',
        order_by='CloseApproachModel.approach_time'
    )
    
    # Обновленные CheckConstraint для поддержки NULL значений
    __table_args__ = (
        UniqueConstraint('designation', name='uq_asteroid_designation'),
        CheckConstraint(
            "aphelion_au IS NULL OR perihelion_au IS NULL OR aphelion_au > perihelion_au",
            name='check_aphelion_gt_perihelion'
        ),
        CheckConstraint(
            "earth_moid_au IS NULL OR earth_moid_au >= 0",
            name='check_moid_non_negative'
        ),
        CheckConstraint(
            "perihelion_au IS NULL OR perihelion_au > 0",
            name='check_perihelion_positive'
        ),
        CheckConstraint(
            "albedo > 0 AND albedo <= 1",
            name='check_albedo_range'
        ),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Проверка альбедо
        if self.albedo <= 0 or self.albedo > 1:
            raise ValueError(f"Альбедо должно быть в диапазоне (0, 1]. Получено: {self.albedo}")
    
    def __repr__(self) -> str:
        return f"AsteroidModel(id={self.id}, designation={self.designation}, name={self.name})"
        