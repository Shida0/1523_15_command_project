from sqlalchemy import Float, String, ForeignKey, CheckConstraint, Integer, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)

from shared.models.base import Base

class ThreatAssessmentModel(Base):
    """
    Модель для хранения оценок угроз столкновений из NASA Sentry API.
    Соответствует таблице 'threat_assessment_models'.
    """
    
    # Связь с астероидом - ОДИН К ОДНОМУ
    asteroid_id: Mapped[int] = mapped_column(
        ForeignKey('asteroid_models.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
        comment="Ссылка на астероид (One-to-One)"
    )

    # Основные данные из Sentry API
    designation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        default="",
        comment="Обозначение астероида (например, '2023 DW')"
    )
    fullname: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
        comment="Полное название астероида"
    )
    
    # Вероятность и шкалы
    ip: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Вероятность столкновения (impact probability)"
    )
    ts_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Максимальное значение по Туринской шкале"
    )
    ps_max: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Максимальное значение по Палермской шкале"
    )
    
    # Физические характеристики из Sentry (переименованные поля)
    diameter: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Диаметр астероида в километрах (из Sentry)"
    )
    v_inf: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Скорость на бесконечности в км/с"
    )
    h: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Абсолютная звездная величина (H) из Sentry"
    )
    
    # Сценарии столкновений
    n_imp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество сценариев столкновения"
    )
    impact_years: Mapped[List[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Года возможных столкновений (JSON-массив)"
    )
    
    # Наблюдения
    last_obs: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="",
        comment="Дата последнего наблюдения"
    )
    
    # Локализованные данные
    threat_level_ru: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
        comment="Уровень угрозы на русском"
    )
    torino_scale_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Описание по Туринской шкале на русском"
    )
    impact_probability_text_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
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
    
    sentry_last_update: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Время последнего обновления данных из Sentry API"
    )
    
    # Связи
    asteroid: Mapped['AsteroidModel'] = relationship( # type: ignore
        back_populates='threat_assessment',  
        lazy='selectin'
    )
    
    # Ограничения на уровне таблицы
    __table_args__ = (
        UniqueConstraint('asteroid_id', name='uq_threat_assessment_asteroid'),  # One-to-One
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
            "diameter >= 0",
            name='check_diameter_non_negative'
        ),
        CheckConstraint(
            "v_inf >= 0",
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
        """
        Инициализирует экземпляр модели оценки угрозы с валидацией и нормализацией данных.
        
        Args:
            **kwargs: Параметры оценки угрозы для инициализации
        """
        # Поля, которые могут приходить под разными именами
        field_mapping = {
            'diameter_km': 'diameter',  # Threat assessment model has 'diameter' field
            'velocity_km_s': 'v_inf',   # Threat assessment model has 'v_inf' field
            'absolute_magnitude': 'h'   # Threat assessment model has 'h' field
        }
        
        # Применяем маппинг полей
        for old_name, new_name in field_mapping.items():
            if old_name in kwargs and new_name not in kwargs:
                kwargs[new_name] = kwargs.pop(old_name)
        
        # Additional mapping from potential external sources
        # Handle case where asteroid model field names might be passed
        if 'estimated_diameter_km' in kwargs and 'diameter' not in kwargs:
            kwargs['diameter'] = kwargs['estimated_diameter_km']
        
        # Сохраняем переданную энергию
        self.energy_provided = 'energy_megatons' in kwargs
        
        super().__init__(**kwargs)
        
        # Расчет энергии ТОЛЬКО если не была предоставлена
        if not self.energy_provided or self.energy_megatons == 0:
            calculated_energy = self._calculate_energy()
            if calculated_energy > 0:
                self.energy_megatons = calculated_energy
        
        # Автоматическое определение категории воздействия
        if not hasattr(self, 'impact_category') or not self.impact_category:
            self.impact_category = self._determine_impact_category()
        
        # Обеспечиваем наличие threat_level_ru
        if not hasattr(self, 'threat_level_ru') or not self.threat_level_ru:
            self.threat_level_ru = self._assess_threat_level()
    
    def _calculate_energy(self) -> float:
        """Расчет энергии удара в мегатоннах тротила."""
        try:
            # Используем поля с правильными именами
            diameter_km = getattr(self, 'diameter', 0.05)
            velocity_km_s = getattr(self, 'v_inf', 20.0)
            
            if diameter_km <= 0:
                return 0.0
                
            diameter_m = diameter_km * 1000
            radius_m = diameter_m / 2
            
            # Объем в м³
            volume_m3 = (4/3) * 3.14159 * (radius_m ** 3)
            
            # Масса в кг (плотность ~2000 кг/м³ для каменных астероидов)
            mass_kg = volume_m3 * 2000
            
            # Энергия в джоулях
            energy_joules = 0.5 * mass_kg * (velocity_km_s * 1000) ** 2
            
            # Конвертация в мегатонны тротила (1 мегатонна = 4.184e15 джоулей)
            energy_megatons = energy_joules / 4.184e15
            
            return round(energy_megatons, 2)
            
        except (TypeError, ValueError, AttributeError, OverflowError) as e:
            logger.error(f"Error calculating energy for {self.designation}: {e}")
            return 0.0
    
    def _determine_impact_category(self) -> str:
        """Определение категории воздействия на основе энергии."""
        energy = getattr(self, 'energy_megatons', 0.0)
        
        if energy < 1:
            return 'локальный'
        elif energy < 100:
            return 'региональный'
        else:
            return 'глобальный'
    
    def _assess_threat_level(self) -> str:
        """Оценка уровня угрозы на основе шкал Турина и Палермо."""
        ts_max = getattr(self, 'ts_max', 0)
        ps_max = getattr(self, 'ps_max', -10.0)
        
        if ts_max == 0:
            if ps_max < -2:
                return "НУЛЕВОЙ (ниже фонового уровня)"
            else:
                return "ОЧЕНЬ НИЗКИЙ"
        elif 1 <= ts_max <= 4:
            return "НИЗКИЙ (требует наблюдения)"
        elif ts_max == 5:
            return "СРЕДНИЙ (заслуживает внимания астрономов)"
        elif ts_max == 6:
            return "ПОВЫШЕННЫЙ (серьёзная угроза)"
        elif ts_max == 7:
            return "ВЫСОКИЙ (очень серьёзная угроза)"
        elif ts_max >= 8:
            return "КРИТИЧЕСКИЙ (непосредственная угроза)"
        else:
            return "НЕ ОПРЕДЕЛЕН"
    
    def __repr__(self) -> str:
        return f"ThreatAssessmentModel(id={self.id}, asteroid_id={self.asteroid_id}, threat={self.threat_level_ru})"
      