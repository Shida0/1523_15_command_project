# 🚀 **РАЗВЕРТЫВАНИЕ**

## 📋 **ОБЗОР РАЗВЕРТЫВАНИЯ**

В этом разделе описаны процессы настройки, развертывания и эксплуатации системы Asteroid Watch. Включает в себя настройку окружения, конфигурацию, запуск приложения и рекомендации по эксплуатации.

## ⚙️ **НАСТРОЙКА ОКРУЖЕНИЯ**

### **1. Требования к системе**
- Python 3.11 или выше
- PostgreSQL 12 или выше
- pip (для установки зависимостей)
- virtualenv или venv (рекомендуется)

### **2. Установка зависимостей**
```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### **3. Установка дополнительных пакетов для разработки**
```bash
# Установка зависимостей для разработки
pip install -e .

# Установка инструментов для тестирования
pip install pytest pytest-asyncio pytest-cov

# Установка инструментов для форматирования кода
pip install black flake8 mypy
```

## 🗄️ **НАСТРОЙКА БАЗЫ ДАННЫХ**

### **1. Создание базы данных PostgreSQL**
```sql
-- Подключение к PostgreSQL как суперпользователь
CREATE USER asteroid_user WITH PASSWORD 'secure_password';
CREATE DATABASE asteroid_db OWNER asteroid_user;
GRANT ALL PRIVILEGES ON DATABASE asteroid_db TO asteroid_user;
```

### **2. Настройка конфигурации базы данных**
Создайте файл `config.yaml` в корне проекта:

```yaml
database:
  host: "localhost"
  port: 5432
  user: "asteroid_user"
  password: "secure_password"
  db_name: "asteroid_db"

nasa_api:
  base_url: "https://api.nasa.gov"
  rate_limit_requests: 1000
  rate_limit_period: 3600
  timeout: 30
  retry_attempts: 3
  sbdb_timeout: 60
  cad_timeout: 120
  sentry_timeout: 180

application:
  environment: "development"
  log_level: "INFO"
  debug: true
  update_interval_minutes: 60
  max_concurrent_updates: 5
  enable_monitoring: true
  monitoring_port: 8000
```

### **3. Инициализация базы данных**
```bash
# Используя скрипт инициализации из проекта
bash create_db.sh

# Или вручную через alembic (если используется)
alembic upgrade head
```

## 🚀 **ЗАПУСК ПРИЛОЖЕНИЯ**

### **1. Запуск в режиме разработки**
```bash
# Установка переменной окружения для пути к конфигурации
export CONFIG_PATH=./config.yaml

# Запуск приложения через uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Запуск в режиме продакшн**
```bash
# Запуск с настройками продакшн
export CONFIG_PATH=./prod_config.yaml
export PYTHONPATH=/path/to/project:$PYTHONPATH

# Запуск через uvicorn с производительными настройками
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --timeout-keep-alive 30
```

### **3. Запуск с использованием Docker**
Создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CONFIG_PATH=/app/config.yaml
    depends_on:
      - db
    volumes:
      - ./config.yaml:/app/config.yaml

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: asteroid_db
      POSTGRES_USER: asteroid_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Запуск через Docker:
```bash
docker-compose up -d
```

## 🧪 **ТЕСТИРОВАНИЕ В РАЗВЕРТЫВАНИИ**

### **1. Запуск тестов в окружении развертывания**
```bash
# Запуск всех тестов
pytest

# Запуск тестов с покрытием
pytest --cov=. --cov-report=html

# Запуск интеграционных тестов (требуется работающая БД)
pytest tests/integration/ -v
```

### **2. Проверка работоспособности API**
```bash
# Проверка состояния API
curl http://localhost:8000/health

# Проверка получения астероидов
curl http://localhost:8000/asteroids?limit=10

# Проверка получения сближений
curl http://localhost:8000/approaches?limit=10
```

## 🔄 **ОБНОВЛЕНИЕ ДАННЫХ**

### **1. Ручное обновление данных из NASA API**
```python
# Пример скрипта для обновления данных
import asyncio
from shared.external_api.clients.sbdb_api import NASASBDBClient
from shared.external_api.clients.cad_api import CADClient
from shared.external_api.clients.sentry_api import SentryClient
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal
from datetime import datetime, timedelta

async def update_asteroid_data():
    """Обновление данных об астероидах из NASA API"""
    print("Начало обновления данных об астероидах...")
    
    async with NASASBDBClient() as client:
        asteroids = await client.get_asteroids(limit=100)
        print(f"Получено {len(asteroids)} астероидов из NASA SBDB")
    
    async with UnitOfWork(AsyncSessionLocal) as uow:
        created, updated = await uow.asteroid_repo.bulk_create_asteroids(asteroids)
        await uow.commit()
        print(f"Обновлено: создано {created}, обновлено {updated}")
    
    print("Обновление данных об астероидах завершено.")

async def update_approach_data():
    """Обновление данных о сближениях из NASA API"""
    print("Начало обновления данных о сближениях...")
    
    async with CADClient() as client:
        approaches = await client.get_close_approaches(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
            max_distance_au=0.05
        )
        total_approaches = sum(len(v) for v in approaches.values())
        print(f"Получено {total_approaches} сближений из NASA CAD")
    
    # Преобразование данных для сохранения
    all_approaches = []
    async with UnitOfWork(AsyncSessionLocal) as uow:
        for designation, approach_list in approaches.items():
            asteroid = await uow.asteroid_repo.get_by_designation(designation)
            if asteroid:
                for approach in approach_list:
                    approach['asteroid_id'] = asteroid.id
                    all_approaches.append(approach)
        
        if all_approaches:
            created = await uow.approach_repo.bulk_create_approaches(
                all_approaches, 
                f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            await uow.commit()
            print(f"Создано {created} записей о сближениях")
    
    print("Обновление данных о сближениях завершено.")

async def update_threat_data():
    """Обновление данных об угрозах из NASA API"""
    print("Начало обновления данных об угрозах...")
    
    async with SentryClient() as client:
        threats = await client.fetch_current_impact_risks()
        print(f"Получено {len(threats)} угроз из NASA Sentry")
    
    # Преобразование данных для сохранения
    threats_to_save = []
    async with UnitOfWork(AsyncSessionLocal) as uow:
        for threat in threats:
            asteroid = await uow.asteroid_repo.get_by_designation(threat.designation)
            if asteroid:
                threat_dict = threat.to_dict()
                threat_dict['asteroid_id'] = asteroid.id
                threats_to_save.append(threat_dict)
        
        if threats_to_save:
            created, updated = await uow.threat_repo.bulk_create_threats(threats_to_save)
            await uow.commit()
            print(f"Создано {created}, обновлено {updated} записей об угрозах")
    
    print("Обновление данных об угрозах завершено.")

async def full_update():
    """Полное обновление всех данных"""
    print("=== НАЧАЛО ПОЛНОГО ОБНОВЛЕНИЯ ДАННЫХ ===")
    
    await update_asteroid_data()
    await update_approach_data()
    await update_threat_data()
    
    print("=== ПОЛНОЕ ОБНОВЛЕНИЕ ДАННЫХ ЗАВЕРШЕНО ===")

# Запуск обновления
if __name__ == "__main__":
    asyncio.run(full_update())
```

### **2. Настройка регулярного обновления (cron)**
Создайте скрипт `update_data.sh`:

```bash
#!/bin/bash

# Установка переменных окружения
export CONFIG_PATH=/path/to/config.yaml
export PYTHONPATH=/path/to/project:$PYTHONPATH

# Запуск обновления данных
cd /path/to/project
source venv/bin/activate
python scripts/update_data.py

echo "Обновление данных завершено: $(date)"
```

Добавьте в cron для регулярного обновления:
```bash
# Обновление каждый день в 2 часа ночи
0 2 * * * /path/to/project/scripts/update_data.sh >> /var/log/asteroid_update.log 2>&1
```

## 📊 **МОНИТОРИНГ И ЛОГИРОВАНИЕ**

### **1. Настройка логирования**
Конфигурация логирования находится в `config.yaml`:

```yaml
application:
  log_level: "INFO"  # Уровень логирования
  # другие настройки...
```

### **2. Пример настройки логирования в Python**
```python
import logging
import logging.config
import yaml

def setup_logging(config_path: str = 'logging_config.yaml'):
    """Настройка логирования из конфигурационного файла"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

# Пример logging_config.yaml
"""
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/app.log
    maxBytes: 10485760 # 10MB
    backupCount: 20
    encoding: utf8

loggers:
  '': # root logger
    handlers: [console, file]
    level: DEBUG
    propagate: false

  app:
    level: DEBUG
    handlers: [console, file]
    propagate: false
"""
```

### **3. Мониторинг производительности**
```python
# Пример middleware для мониторинга производительности
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        
        processing_time = end_time - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {processing_time:.4f}s")
        
        return response
```

## 🔒 **БЕЗОПАСТЬ И БЕКАПЫ**

### **1. Резервное копирование базы данных**
```bash
# Ежедневный бекап базы данных
pg_dump -h localhost -U asteroid_user -d asteroid_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Скрипт автоматического бекапа
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/asteroid_backup_$DATE.sql"

pg_dump -h localhost -U asteroid_user -d asteroid_db > $BACKUP_FILE

# Удаление бекапов старше 30 дней
find $BACKUP_DIR -name "asteroid_backup_*.sql" -mtime +30 -delete
```

### **2. Защита API ключей**
- Не храните API ключи в коде
- Используйте переменные окружения или безопасные хранилища
- Ограничьте права доступа к конфигурационным файлам

### **3. Обновление безопасности**
```bash
# Проверка уязвимостей в зависимостях
pip install safety
safety check

# Обновление зависимостей
pip list --outdated
pip install --upgrade package_name
```

## 🧪 **ПРОВЕРКА РАЗВЕРТЫВАНИЯ**

### **1. Тестирование производительности**
```bash
# Тестирование нагрузки с помощью Apache Bench
ab -n 1000 -c 10 http://localhost:8000/asteroids?limit=10

# Тестирование с помощью wrk
wrk -t12 -c400 -d30s http://localhost:8000/asteroids?limit=10
```

### **2. Проверка масштабируемости**
- Проверьте работу с несколькими воркерами uvicorn
- Проверьте работу с балансировщиком нагрузки (nginx)
- Проверьте использование connection pool

### **3. Проверка отказоустойчивости**
- Проверьте работу при падении базы данных
- Проверьте работу при превышении лимитов API NASA
- Проверьте восстановление после сбоев

## 🔄 **ОБНОВЛЕНИЕ ПРИЛОЖЕНИЯ**

### **1. Процесс обновления**
```bash
# 1. Остановка текущего приложения
pkill -f uvicorn

# 2. Обновление кода
git pull origin main

# 3. Обновление зависимостей
pip install -r requirements.txt

# 4. Обновление схемы базы данных (если необходимо)
alembic upgrade head

# 5. Запуск обновленного приложения
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **2. Blue-Green деплоймент**
Для минимизации времени простоя можно использовать blue-green деплоймент:

1. Запустить новую версию приложения на другом порту
2. Перенаправить трафик на новую версию
3. Проверить работоспособность новой версии
4. Остановить старую версию

---

**Документация завершена.** Эта документация предоставляет полное руководство по развертыванию и эксплуатации системы Asteroid Watch.