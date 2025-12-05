from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy import DateTime, func
import re

class Base(AsyncAttrs, DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.
    Наследует AsyncAttrs для асинхронной работы и DeclarativeBase.
    """
    
    __abstract__ = True
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Автоматически генерирует имя таблицы из имени класса."""
        name = cls.__name__ # Преобразует CamelCase в snake_case (Asteroid → asteroids)
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return name + 's'
    
    # Общие поля для всех таблиц
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),  # Время создания записи
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),  # Автоматическое обновление при изменении
        nullable=False
    )
    
    def __repr__(self) -> str:
        """Строковое представление объекта для отладки."""
        attrs = []
        for key, value in self.__dict__.items():
            if not key.startswith('_'):                
                if isinstance(value, str) and len(value) > 20: # Ограничиваем длину строковых значений для читаемости
                    value = value[:17] + '...'
                attrs.append(f"{key}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"
    