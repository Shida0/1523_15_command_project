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
        name = cls.__name__
        
        # Улучшенная логика преобразования CamelCase в snake_case
        # Обрабатываем аббревиатуры правильно
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        name = re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2', name)
        name = name.lower()
        
        # Преобразование в множественное число
        if name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            name += 'es'
        elif name.endswith('y') and name[-2] not in 'aeiou':
            name = name[:-1] + 'ies'
        elif name.endswith('f'):
            name = name[:-1] + 'ves'
        elif name.endswith('fe'):
            name = name[:-2] + 'ves'
        else:
            name += 's'
        
        return name
    
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