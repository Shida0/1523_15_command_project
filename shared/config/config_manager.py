import os
import json
import logging
from typing import Optional, Union
from pathlib import Path
from pydantic import BaseModel, ValidationError, Field
import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Конфигурация базы данных. Все параметры берутся ТОЛЬКО из переменных окружения: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME"""
    host: str = Field(default_factory=lambda: os.getenv('DB_HOST'))
    port: int = Field(default_factory=lambda: int(os.getenv('DB_PORT', '5432')))
    user: str = Field(default_factory=lambda: os.getenv('DB_USER'))
    password: str = Field(default_factory=lambda: os.getenv('DB_PASSWORD'))
    db_name: str = Field(default_factory=lambda: os.getenv('DB_NAME'))

    @property
    def dsn(self) -> str:
        """Получить строку подключения к базе данных"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"

    @property
    def async_driver(self) -> str:
        """Получить драйвер для асинхронного подключения"""
        return "asyncpg"

    def validate_required(self) -> None:
        """Проверить что все обязательные параметры заданы"""
        missing = []
        if not self.host:
            missing.append('DB_HOST')
        if not self.user:
            missing.append('DB_USER')
        if not self.password:
            missing.append('DB_PASSWORD')
        if not self.db_name:
            missing.append('DB_NAME')
        
        if missing:
            raise ValueError(
                f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}. "
                "Создайте файл .env и добавьте необходимые переменные."
            )


class NasaApiConfig(BaseModel):
    """Конфигурация API NASA"""
    base_url: str = Field(default="https://api.nasa.gov")
    rate_limit_requests: int = Field(default=1000)
    rate_limit_period: int = Field(default=3600)
    timeout: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    sbdb_timeout: int = Field(default=60)
    cad_timeout: int = Field(default=120)
    sentry_timeout: int = Field(default=180)


class ApplicationConfig(BaseModel):
    """Конфигурация на уровне приложения"""
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    update_interval_minutes: int = Field(default=60)
    max_concurrent_updates: int = Field(default=5)
    enable_monitoring: bool = Field(default=True)
    monitoring_port: int = Field(default=8000)


class ConfigManager:
    """
    Централизованный менеджер конфигурации.
    
    Параметры БД загружаются только из переменных окружения (.env).
    Настройки приложения и NASA API могут быть загружены из config.yaml.
    """

    def __init__(self):
        self.database: DatabaseConfig = DatabaseConfig()
        self.nasa_api: NasaApiConfig = NasaApiConfig()
        self.application: ApplicationConfig = ApplicationConfig()
        self._loaded_from: str = "defaults"

    def load_from_file(self, config_path: Union[str, Path]) -> 'ConfigManager':
        """
        Загрузка конфигурации приложения из файла YAML или JSON.
        
        ВАЖНО: Параметры базы данных НЕ загружаются из файла.
        Они берутся только из переменных окружения (.env).
        
        Из файла загружаются:
        - nasa_api: настройки NASA API
        - application: настройки приложения
        """
        try:
            config_path = Path(config_path)

            if not config_path.exists():
                logger.warning(f"Файл конфигурации не найден: {config_path}. Используются значения по умолчанию.")
                return self

            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                raise ValueError(f"Неподдерживаемый формат файла конфигурации: {config_path.suffix}")

            if 'nasa_api' in config_data:
                self.nasa_api = NasaApiConfig(**config_data['nasa_api'])

            if 'application' in config_data:
                self.application = ApplicationConfig(**config_data['application'])

            self._loaded_from = str(config_path)
            logger.info(f"Конфигурация приложения загружена из файла: {config_path}")

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
        """Валидация текущей конфигурации"""
        try:
            # Проверяем обязательные параметры БД
            self.database.validate_required()
            self.database.model_validate(self.database.model_dump())
            self.nasa_api.model_validate(self.nasa_api.model_dump())
            self.application.model_validate(self.application.model_dump())
            return True
        except ValidationError as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            return False
        except ValueError as e:
            logger.error(f"Ошибка конфигурации: {e}")
            return False

    def get_database_url(self) -> str:
        """Получить URL базы данных"""
        return self.database.dsn

    def get_log_level(self) -> str:
        """Получить настроенный уровень логирования"""
        return self.application.log_level.upper()

    def is_production(self) -> bool:
        """Проверить, запущено ли в производственном окружении"""
        return self.application.environment.lower() == 'production'

    def __str__(self) -> str:
        return f"ConfigManager(loaded_from='{self._loaded_from}', env='{self.application.environment}')"

    def __repr__(self) -> str:
        return self.__str__()


_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Получить глобальный экземпляр конфигурации.
    
    Параметры БД загружаются из .env файла.
    Настройки приложения загружаются из config.yaml (если указан в CONFIG_PATH).
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
        
        # Сначала загружаем параметры БД из .env (уже сделано через load_dotenv())
        # Проверяем что все обязательные параметры БД заданы
        _config_instance.database.validate_required()
        
        # Затем загружаем настройки приложения из файла
        config_path = os.getenv('CONFIG_PATH', './config.yaml')
        _config_instance.load_from_file(config_path)
        
    return _config_instance


def set_config(config: ConfigManager) -> None:
    """Установить глобальный экземпляр конфигурации"""
    global _config_instance
    _config_instance = config
