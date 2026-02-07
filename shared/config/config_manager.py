"""
Система управления конфигурацией для приложения мониторинга астероидов.
"""
import os
import json
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path
from pydantic import BaseModel, ValidationError, Field
from pydantic_settings import BaseSettings
import yaml


logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Конфигурация базы данных."""
    host: str = Field(default="localhost", description="Хост базы данных")
    port: int = Field(default=5432, description="Порт базы данных")
    user: str = Field(default="asteroid_user", description="Пользователь базы данных")
    password: str = Field(default="", description="Пароль к базе данных")
    db_name: str = Field(default="asteroid_db", description="Имя базы данных")

    @property
    def dsn(self) -> str:
        """Получить строку подключения к базе данных."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


class NasaApiConfig(BaseModel):
    """Конфигурация API NASA."""
    base_url: str = Field(default="https://api.nasa.gov", description="Базовый URL API NASA")
    rate_limit_requests: int = Field(default=1000, description="Максимальное количество запросов в час")
    rate_limit_period: int = Field(default=3600, description="Период ограничения частоты в секундах")
    timeout: int = Field(default=30, description="Таймаут запроса в секундах")
    retry_attempts: int = Field(default=3, description="Количество попыток повтора")
    sbdb_timeout: int = Field(default=60, description="Таймаут API SBDB")
    cad_timeout: int = Field(default=120, description="Таймаут API CAD")
    sentry_timeout: int = Field(default=180, description="Таймаут API Sentry")


class ApplicationConfig(BaseModel):
    """Конфигурация на уровне приложения."""
    environment: str = Field(default="development", description="Окружение (dev, prod, test)")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    debug: bool = Field(default=False, description="Режим отладки")
    update_interval_minutes: int = Field(default=60, description="Интервал обновления данных в минутах")
    max_concurrent_updates: int = Field(default=5, description="Максимальное количество одновременных операций обновления")
    enable_monitoring: bool = Field(default=True, description="Включить мониторинг приложения")
    monitoring_port: int = Field(default=8000, description="Порт для точки мониторинга")


class ConfigManager:
    """Централизованный менеджер конфигурации с возможностями валидации и загрузки."""
    
    def __init__(self):
        self.database: DatabaseConfig = DatabaseConfig()
        self.nasa_api: NasaApiConfig = NasaApiConfig()
        self.application: ApplicationConfig = ApplicationConfig()
        self._loaded_from: str = "defaults"
        
    def load_from_file(self, config_path: Union[str, Path]) -> 'ConfigManager':
        """Загрузка конфигурации из файла YAML или JSON."""
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")
            
            # Определение типа файла и загрузка
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                raise ValueError(f"Неподдерживаемый формат файла конфигурации: {config_path.suffix}")
            
            # Валидация и установка конфигурации
            if 'database' in config_data:
                self.database = DatabaseConfig(**config_data['database'])
            
            if 'nasa_api' in config_data:
                self.nasa_api = NasaApiConfig(**config_data['nasa_api'])
            
            if 'application' in config_data:
                self.application = ApplicationConfig(**config_data['application'])
            
            self._loaded_from = str(config_path)
            logger.info(f"Конфигурация загружена из файла: {config_path}")
            
            # Обновляем таймауты NASA API из конфигурации
            try:
                from shared.resilience.timeout import update_nasa_api_timeouts_from_values
                update_nasa_api_timeouts_from_values(self.nasa_api)
            except ImportError:
                logger.warning("Could not update NASA API timeouts from config")
            
            return self
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации из файла: {e}")
            raise
    
    def validate(self) -> bool:
        """Валидация текущей конфигурации."""
        try:
            # Валидация каждого раздела конфигурации
            self.database.model_validate(self.database.model_dump())
            self.nasa_api.model_validate(self.nasa_api.model_dump())
            self.application.model_validate(self.application.model_dump())
            return True
        except ValidationError as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            return False
    
    def get_database_url(self) -> str:
        """Получить URL базы данных."""
        return self.database.dsn
    
    def get_log_level(self) -> str:
        """Получить настроенный уровень логирования."""
        return self.application.log_level.upper()
    
    def is_production(self) -> bool:
        """Проверить, запущено ли в производственном окружении."""
        return self.application.environment.lower() == 'production'
    
    def __str__(self) -> str:
        return f"ConfigManager(loaded_from='{self._loaded_from}', env='{self.application.environment}')"
    
    def __repr__(self) -> str:
        return self.__str__()


# Глобальный экземпляр конфигурации
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Получить глобальный экземпляр конфигурации."""
    global _config_instance
    if _config_instance is None:
        config_path = os.getenv('CONFIG_PATH', './config.yaml')
        _config_instance = ConfigManager().load_from_file(config_path)
    return _config_instance


def set_config(config: ConfigManager) -> None:
    """Установить глобальный экземпляр конфигурации."""
    global _config_instance
    _config_instance = config
