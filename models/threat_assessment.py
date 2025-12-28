from sqlalchemy import Float, String, ForeignKey, CheckConstraint, Integer, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

from .base import Base

class ThreatAssessmentModel(Base):
    """
    Модель для хранения оценок угроз столкновений из NASA Sentry API.
    Соответствует таблице 'threat_assessment_models'.
    """
    
    # Связь с астероидом (в Sentry угрозы привязаны к астероидам)
    asteroid_id: Mapped[int] = mapped_column(
        ForeignKey('asteroid_models.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Ссылка на астероид"
    )
    
    # Основные данные из Sentry API
    designation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Обозначение астероида (например, '2023 DW')"
    )
    fullname: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Полное название астероида"
    )
    
    # Вероятность и шкалы
    ip: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Вероятность столкновения (impact probability)"
    )
    ts_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Максимальное значение по Туринской шкале"
    )
    ps_max: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Максимальное значение по Палермской шкале"
    )
    
    # Физические характеристики из Sentry
    diameter_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Диаметр астероида в километрах (из Sentry)"
    )
    velocity_km_s: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Скорость на бесконечности в км/с"
    )
    absolute_magnitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Абсолютная звездная величина (H) из Sentry"
    )
    
    # Сценарии столкновений
    n_imp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество сценариев столкновения"
    )
    impact_years: Mapped[List[int]] = mapped_column(
        JSON,
        nullable=False,
        comment="Года возможных столкновений (JSON-массив)"
    )
    
    # Наблюдения
    last_obs: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Дата последнего наблюдения"
    )
    
    # Локализованные данные
    threat_level_ru: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Уровень угрозы на русском"
    )
    torino_scale_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Описание по Туринской шкале на русском"
    )
    impact_probability_text_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст вероятности на русском"
    )
    
    # Энергетические параметры (расчетные)
    energy_megatons: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Энергия воздействия в мегатоннах тротила"
    )
    impact_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='локальный',
        comment="Категория воздействия: 'локальный', 'региональный', 'глобальный'"
    )
    
    # Связи
    asteroid: Mapped['AsteroidModel'] = relationship( # type: ignore
        back_populates='threat_assessments',
        lazy='selectin'
    )
    
    # Ограничения на уровне таблицы
    __table_args__ = (
        UniqueConstraint('designation', name='uq_threat_assessment_designation'),
        CheckConstraint(
            "ts_max >= 0 AND ts_max <= 10",
            name='check_torino_scale_range'
        ),
        CheckConstraint(
            "ip >= 0",
            name='check_probability_non_negative'
        ),
        CheckConstraint(
            "diameter_km >= 0",
            name='check_diameter_non_negative'
        ),
        CheckConstraint(
            "velocity_km_s >= 0",
            name='check_velocity_non_negative'
        ),
        CheckConstraint(
            "n_imp >= 0",
            name='check_n_imp_non_negative'
        ),
        CheckConstraint(
            "energy_megatons >= 0",
            name='check_energy_non_negative'
        ),
        CheckConstraint(
            "impact_category IN ('локальный', 'региональный', 'глобальный')",
            name='check_impact_category'
        ),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Автоматический расчет энергии, если не задано
        if not hasattr(self, 'energy_megatons') or self.energy_megatons == 0:
            self.energy_megatons = self._calculate_energy()
        
        # Автоматическое определение категории воздействия
        if not hasattr(self, 'impact_category') or not self.impact_category:
            self.impact_category = self._determine_impact_category()
        
        # Обеспечиваем наличие threat_level_ru
        if not hasattr(self, 'threat_level_ru') or not self.threat_level_ru:
            self.threat_level_ru = self._assess_threat_level()
    
    def _calculate_energy(self) -> float:
        """Расчет энергии удара в мегатоннах тротила."""
        # Формула: E = 0.5 * m * v^2
        # m = объем * плотность, плотность астероидов ~ 2 г/см³ = 2000 кг/м³
        # Объем сферы = (4/3) * π * r^3
        
        # Диаметр в метрах
        diameter_m = self.diameter_km * 1000
        radius_m = diameter_m / 2
        
        # Объем в м³
        volume_m3 = (4/3) * 3.14159 * (radius_m ** 3)
        
        # Масса в кг (плотность ~2000 кг/м³)
        mass_kg = volume_m3 * 2000
        
        # Энергия в джоулях
        energy_joules = 0.5 * mass_kg * (self.velocity_km_s * 1000) ** 2
        
        # Конвертация в мегатонны тротила (1 мегатонна = 4.184e15 джоулей)
        energy_megatons = energy_joules / 4.184e15
        
        return round(energy_megatons, 2)
    
    def _determine_impact_category(self) -> str:
        """Определение категории воздействия на основе энергии."""
        if self.energy_megatons < 1:
            return 'локальный'
        elif self.energy_megatons < 100:
            return 'региональный'
        else:
            return 'глобальный'
    
    def _assess_threat_level(self) -> str:
        """Оценка уровня угрозы на основе шкал Турина и Палермо."""
        if self.ts_max == 0:
            if self.ps_max < -2:
                return "НУЛЕВОЙ (ниже фонового уровня)"
            else:
                return "ОЧЕНЬ НИЗКИЙ"
        elif 1 <= self.ts_max <= 4:
            return "НИЗКИЙ (требует наблюдения)"
        elif self.ts_max == 5:
            return "СРЕДНИЙ (заслуживает внимания астрономов)"
        elif self.ts_max == 6:
            return "ПОВЫШЕННЫЙ (серьёзная угроза)"
        elif self.ts_max == 7:
            return "ВЫСОКИЙ (очень серьёзная угроза)"
        elif self.ts_max >= 8:
            return "КРИТИЧЕСКИЙ (непосредственная угроза)"
        else:
            return "НЕОПРЕДЕЛЕН"
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь для API."""
        return {
            'designation': self.designation,
            'fullname': self.fullname,
            'ip': self.ip,
            'ts_max': self.ts_max,
            'ps_max': self.ps_max,
            'diameter_km': self.diameter_km,
            'velocity_km_s': self.velocity_km_s,
            'absolute_magnitude': self.absolute_magnitude,
            'n_imp': self.n_imp,
            'impact_years': self.impact_years,
            'last_obs': self.last_obs,
            'threat_level_ru': self.threat_level_ru,
            'torino_scale_ru': self.torino_scale_ru,
            'impact_probability_text_ru': self.impact_probability_text_ru,
            'energy_megatons': self.energy_megatons,
            'impact_category': self.impact_category,
            'asteroid_id': self.asteroid_id
        }
    
    def __repr__(self) -> str:
        return f"ThreatAssessmentModel(id={self.id}, designation={self.designation}, threat={self.threat_level_ru})"
    
    