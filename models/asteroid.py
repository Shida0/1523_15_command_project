import logging
from sqlalchemy import CheckConstraint, Float, String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from .base import Base

logger = logging.getLogger(__name__)

class AsteroidModel(Base):
    """
    Модель для хранения данных о потенциально опасных астероидах (PHA).
    Соответствует таблице 'asteroid_models'.
    """
    
    # Основные идентификаторы
    designation: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Обозначение NASA (напр., '99942', '2025 XN4')"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Собственное название астероида (напр., 'Apophis')"
    )
    
    # Орбитальные параметры
    perihelion_au: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Расстояние перигелия в астрономических единицах"
    )
    aphelion_au: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Расстояние афелия в астрономических единицах"
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
        comment="Диаметр точный или же рассчитан по стандартному альбедо"
    )
    albedo: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Альбедо (отражательная способность), если известно"
    )
    diameter_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='calculated',
        comment="Источник данных о диаметре: 'measured', 'computed', 'calculated'"
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
    close_approaches: Mapped[List['CloseApproachModel']] = relationship( # type: ignore
        back_populates='asteroid',
        cascade='all, delete-orphan',
        lazy='selectin',
        order_by='CloseApproachModel.approach_time'
    )
    # В класс AsteroidModel добавляем/изменяем связь:
    threat_assessment: Mapped[Optional['ThreatAssessmentModel']] = relationship( # type: ignore
        back_populates='asteroid',
        cascade='all, delete-orphan',
        lazy='selectin',
        uselist=False  # КРИТИЧЕСКИ ВАЖНО: Один объект, не список!
    )
    
    # Обновленные CheckConstraint с добавленными полями (УБРАН UniqueConstraint на mpc_number)
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
        CheckConstraint(
            "diameter_source IN ('measured', 'computed', 'calculated')",
            name='check_diameter_source'
        ),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # валидация альбедо
        if self.albedo is None:
            # Значение не было передано - используем по умолчанию
            self.albedo = 0.15
            logger.debug(f"Albedo not provided for {self.designation}, using default 0.15")
        elif isinstance(self.albedo, (int, float)):
            # Значение передано как число - проверяем диапазон
            self.albedo = float(self.albedo)
            if not (0 < self.albedo <= 1):
                logger.warning(f"Albedo {self.albedo} out of range (0,1] for {self.designation}, using 0.15")
                self.albedo = 0.15
        else:
            # Пытаемся преобразовать строку или другой тип
            try:
                self.albedo = float(self.albedo)
                if not (0 < self.albedo <= 1):
                    logger.warning(f"Albedo {self.albedo} out of range for {self.designation}, using 0.15")
                    self.albedo = 0.15
            except (ValueError, TypeError):
                logger.warning(f"Cannot convert albedo '{self.albedo}' to float for {self.designation}, using 0.15")
                self.albedo = 0.15
        
        # валидация diameter_source
        valid_sources = {'measured', 'computed', 'calculated'}
        if self.diameter_source not in valid_sources:
            logger.warning(f"Invalid diameter_source '{self.diameter_source}' for {self.designation}, using 'calculated'")
            self.diameter_source = 'calculated'
        
        # Диаметр
        if not hasattr(self, 'estimated_diameter_km') or self.estimated_diameter_km is None:
            self.estimated_diameter_km = 0.05
        else:
            try:
                self.estimated_diameter_km = float(self.estimated_diameter_km)
                if self.estimated_diameter_km <= 0:
                    logger.warning(f"Invalid diameter {self.estimated_diameter_km} for {self.designation}, using 0.05")
                    self.estimated_diameter_km = 0.05
            except (TypeError, ValueError):
                logger.warning(f"Cannot convert diameter '{self.estimated_diameter_km}' to float for {self.designation}, using 0.05")
                self.estimated_diameter_km = 0.05
        
        # Абсолютная величина
        if not hasattr(self, 'absolute_magnitude') or self.absolute_magnitude is None:
            self.absolute_magnitude = 18.0
        else:
            try:
                self.absolute_magnitude = float(self.absolute_magnitude)
            except (TypeError, ValueError):
                logger.warning(f"Cannot convert absolute_magnitude '{self.absolute_magnitude}' for {self.designation}, using 18.0")
                self.absolute_magnitude = 18.0
    
    def __repr__(self) -> str:
        return f"AsteroidModel(id={self.id}, designation={self.designation}, name={self.name})"