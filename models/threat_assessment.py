from sqlalchemy import Float, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .base import Base

class ThreatAssessmentModel(Base):
    """
    Модель для хранения оценок опасности сближений.
    Соответствует таблице 'threat_assessment_models'.
    """
    
    # Связь со сближением (один-к-одному)
    approach_id: Mapped[int] = mapped_column(
        ForeignKey('close_approach_models.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True,
        comment="Ссылка на сближение (уникальная)"
    )
    
    # Уровень угрозы
    threat_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Уровень угрозы: 'низкий', 'средний', 'высокий', 'критический'"
    )
    
    # Категория воздействия
    impact_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Категория воздействия: 'локальный', 'региональный', 'глобальный'"
    )
    
    # Энергетические параметры
    energy_megatons: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Энергия воздействия в мегатоннах тротила"
    )
    
    # Входные данные для расчета (для отслеживания)
    calculation_input_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=True,
        comment="Хеш входных данных для отслеживания изменений"
    )
    
    # Связи
    close_approach: Mapped['CloseApproachModel'] = relationship(
        back_populates='threat_assessment',
        lazy='selectin'
    )
    
    # Ограничения на уровне таблицы
    __table_args__ = (
        CheckConstraint(
            "threat_level IN ('низкий', 'средний', 'высокий', 'критический')",
            name='check_threat_level'
        ),
        CheckConstraint(
            "impact_category IN ('локальный', 'региональный', 'глобальный')",
            name='check_impact_category'
        ),
        CheckConstraint(
            "energy_megatons >= 0",
            name='check_energy_non_negative'
        ),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Автоматическое вычисление хеша входных данных
        if 'calculation_input_hash' not in kwargs:
            self.calculation_input_hash = self._calculate_input_hash()
    
    def _calculate_input_hash(self) -> str:
        """Вычисляет хеш входных данных для отслеживания изменений."""
        import hashlib
        threat_level = getattr(self, 'threat_level', '')
        impact_category = getattr(self, 'impact_category', '')
        energy = getattr(self, 'energy_megatons', 0.0)
        input_data = f"{threat_level}:{impact_category}:{energy}"
        return hashlib.sha256(input_data.encode()).hexdigest()
    
    def update_hash(self):
        """Обновляет хеш при изменении данных."""
        # Не обновляем, если хеш был задан явно
        if not hasattr(self, '_custom_hash') or not self._custom_hash:
            self.calculation_input_hash = self._calculate_input_hash()
    
    def __setattr__(self, name, value):
        """Перехватываем установку атрибутов для обновления хеша."""
        # Вызываем родительский метод
        super().__setattr__(name, value)
        
        # Если изменились поля, влияющие на хеш
        if name in ['threat_level', 'impact_category', 'energy_megatons']:
            # Проверяем, был ли хеш задан явно
            if not hasattr(self, '_custom_hash'):
                self._custom_hash = False
            
            if not self._custom_hash:
                self.update_hash()