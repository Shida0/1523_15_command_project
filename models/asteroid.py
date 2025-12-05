from sqlalchemy import CheckConstraint, Float, String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from .base import Base

class AsteroidModel(Base):
    """
    Модель для хранения данных о потенциально опасных астероидах (PHA).
    Соответствует таблице 'asteroid_models' (автоматически из Base).
    """
    
    # Основные идентификаторы
    mpc_number: Mapped[int] = mapped_column(
        unique=True, 
        nullable=False,
        comment="Уникальный номер из каталога Minor Planet Center"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Собственное название астероида"
    )
    designation: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        comment="Временное обозначение"
    )
    
    # Орбитальные параметры
    perihelion_au: Mapped[float] = mapped_column(
        Float, 
        nullable=False,
        comment="Расстояние перигелия в астрономических единицах"
    )
    aphelion_au: Mapped[float] = mapped_column(
        Float, 
        nullable=False,
        comment="Расстояние афелия в астрономических единицах"
    )
    earth_moid_au: Mapped[float] = mapped_column(
        Float, 
        nullable=False,
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
    albedo: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Альбедо (отражательная способность), если известно"
    )
    
    # Классификация
    is_neo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Является ли околоземным объектом (NEO)"
    )
    is_pha: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Является ли потенциально опасным (PHA)"
    )
    
    # Дополнительные данные
    orbit_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Дополнительные орбитальные параметры в формате JSON"
    )
    last_orbit_update: Mapped[Optional[datetime]] = mapped_column(
        comment="Дата последнего обновления орбитальных данных из внешних источников"
    )
    
    # Связи с другими таблицами
    close_approaches: Mapped[List['CloseApproachModel']] = relationship(
        back_populates='asteroid',
        cascade='all, delete-orphan',
        lazy='selectin',
        order_by='CloseApproachModel.approach_time'
    )
    
    # Добавьте CheckConstraint в __table_args__
    __table_args__ = (
        CheckConstraint(
            "aphelion_au > perihelion_au",
            name='check_aphelion_gt_perihelion'
        ),
        CheckConstraint(
            "earth_moid_au >= 0",
            name='check_moid_non_negative'
        ),
        CheckConstraint(
            "perihelion_au > 0",
            name='check_perihelion_positive'
        ),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Автоматическая проверка: афелий всегда больше перигелия
        if self.aphelion_au <= self.perihelion_au:
            raise ValueError(
                f"Афелий ({self.aphelion_au}) должен быть больше перигелия ({self.perihelion_au})"
            )
            
            