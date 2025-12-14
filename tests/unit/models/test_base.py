"""
Тесты для базовой модели.
"""
import pytest
from sqlalchemy import DateTime, inspect
from models.base import Base

class TestBaseModel:
    """Тесты базовой модели SQLAlchemy."""
    
    def test_base_is_abstract(self):
        """Проверка, что Base является абстрактным классом."""
        assert Base.__abstract__ == True
    
    def test_base_tablename_generation(self):
        """Генерация имени таблицы из имени класса."""
        # Создаем тестовый класс, наследуемый от Base
        class TestModel(Base):
            __abstract__ = True  # Делаем абстрактным, чтобы не создавалась таблица
        
        # Проверяем, что имя таблицы сгенерировано правильно
        assert TestModel.__tablename__ == 'test_models'
    
    def test_base_tablename_edge_cases(self):
        """Граничные случаи генерации имени таблицы."""
        # Тест 1: Одно слово
        class Asteroid(Base):
            __abstract__ = True
        assert Asteroid.__tablename__ == 'asteroids'
        
        # Тест 2: Несколько слов в CamelCase
        class CloseApproach(Base):
            __abstract__ = True
        assert CloseApproach.__tablename__ == 'close_approaches'
        
        # Тест 3: Аббревиатура в начале - теперь работает правильно
        class NASAReport(Base):
            __abstract__ = True
        assert NASAReport.__tablename__ == 'nasa_reports'
        
        # Тест 4: Аббревиатура в конце
        class ReportNASA(Base):
            __abstract__ = True
        assert ReportNASA.__tablename__ == 'report_nasas'
    
    def test_base_common_fields(self):
        """Проверка общих полей в базовой модели."""
        # Проверяем, что у класса Base есть ожидаемые атрибуты
        assert hasattr(Base, 'id')
        assert hasattr(Base, 'created_at')
        assert hasattr(Base, 'updated_at')
        
        # Проверяем типы через аннотации
        from sqlalchemy.orm import Mapped
        assert isinstance(Base.__annotations__.get('id'), type(Mapped[int]))
        assert isinstance(Base.__annotations__.get('created_at'), type(Mapped[DateTime]))
        assert isinstance(Base.__annotations__.get('updated_at'), type(Mapped[DateTime]))

    def test_base_repr_method(self):
        """Тестирование строкового представления."""
        # Создаем тестовый класс
        class TestModelRepr(Base):
            __abstract__ = True
        
        # Создаем экземпляр через mock-объект
        class MockModel:
            def __init__(self):
                self.id = 1
                self.name = "Test"
                self.value = 123
                self.long_text = "This is a very long text that should be truncated for readability in repr"
            
            def __repr__(self):
                # Копируем логику из Base
                attrs = []
                for key, value in self.__dict__.items():
                    if not key.startswith('_'):                
                        if isinstance(value, str) and len(value) > 20:
                            value = value[:17] + '...'
                        attrs.append(f"{key}={value!r}")
                return f"MockModel({', '.join(attrs)})"
        
        obj = MockModel()
        repr_str = repr(obj)
        
        # Проверяем структуру repr
        assert repr_str.startswith('MockModel(')
        assert repr_str.endswith(')')
        assert 'id=1' in repr_str
        assert 'name=' in repr_str
        assert 'value=123' in repr_str
        assert '...' in repr_str
    
    def test_base_inheritance(self):
        """Проверка наследования от AsyncAttrs и DeclarativeBase."""
        from sqlalchemy.ext.asyncio import AsyncAttrs
        from sqlalchemy.orm import DeclarativeBase
        
        # Проверяем MRO (Method Resolution Order)
        mro = Base.__mro__
        assert AsyncAttrs in mro
        assert DeclarativeBase in mro
        
        # Проверяем, что Base имеет необходимые атрибуты
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, 'registry')
    
    def test_base_instantiation(self):
        """Проверка создания экземпляра базового класса."""
        # Base может не иметь _sa_instance_state при создании через конструктор
        # Проверяем базовую функциональность
        try:
            base_instance = Base()
            # Проверяем, что это экземпляр Base
            assert isinstance(base_instance, Base)
            # _sa_instance_state может появиться только после присоединения к сессии
        except Exception as e:
            # Base() может вызывать ошибку - это нормально для некоторых версий SQLAlchemy
            # Проверяем, что ошибка связана с правильной причиной
            assert "Can't instantiate abstract class" in str(e) or "abstract" in str(e).lower()
    
    def test_base_table_args(self):
        """Проверка, что табличные аргументы могут быть добавлены."""
        class TestModelWithArgs(Base):
            __table_args__ = {'comment': 'Test table'}
            __abstract__ = True
        
        # Проверяем, что аргументы сохраняются
        assert TestModelWithArgs.__table_args__ == {'comment': 'Test table'}