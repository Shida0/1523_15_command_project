# 🌌 Asteroid Watch

**Asteroid Watch** — это система мониторинга потенциально опасных астероидов (PHA), которая автоматически собирает данные из открытых API NASA, анализирует их и предоставляет удобный REST API для доступа к информации об астероидах, их сближениях с Землёй и оценках угроз столкновения.

Проект разработан как учебный пример применения современных Python-технологий (FastAPI, SQLAlchemy, Pydantic) и паттернов проектирования (DDD, Repository, Unit of Work).

---

## ✨ Возможности

- **Получение данных из NASA**:
  - SBDB API — информация об астероидах (орбита, размер, альбедо, класс)
  - CAD API — данные о сближениях с Землёй на ближайшие 10 лет
  - Sentry API — оценки рисков столкновения (Туринская и Палермская шкалы)
- **Хранение в PostgreSQL** с использованием асинхронной SQLAlchemy
- **REST API** с пагинацией, фильтрацией и детальными ответами
- **Готовые эндпоинты**:
  - Астероиды: поиск по обозначению, классу орбиты, размеру, MOID
  - Сближения: ближайшие по времени, самые близкие по расстоянию, быстрейшие, за период
  - Угрозы: текущие риски, высокорисковые, по вероятности и энергии
- **Автоматическое обновление данных** (скрипты и планировщик)
- **Отказоустойчивость**: повторные попытки, таймауты, circuit breaker
- **Доменная архитектура** (DDD) с чётким разделением ответственности

---

## 🛠 Технологический стек

- Python 3.11+
- FastAPI
- SQLAlchemy (асинхронная)
- PostgreSQL
- aiohttp
- Pydantic
- Alembic (миграции БД)
- Uvicorn
- Docker / docker-compose (опционально)

---

## 📋 Предварительные требования

Убедитесь, что на вашем компьютере установлены:

- **Python** версии 3.11 или выше
- **PostgreSQL** версии 12 или выше
- **pip** (менеджер пакетов Python)
- **virtualenv** (рекомендуется) или venv

Проверить можно командами:
```bash
python --version
psql --version
pip --version
```

---

## 🚀 Пошаговая установка и запуск с нуля

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/your-username/asteroid-watch.git
cd asteroid-watch
```

### 2. Создайте и активируйте виртуальное окружение

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

> Если файла `requirements.txt` ещё нет, создайте его на основе зависимостей из документации. Примерное содержимое:
> ```
> fastapi==0.115.12
> uvicorn[standard]==0.34.0
> sqlalchemy==2.0.40
> asyncpg==0.30.0
> pydantic==2.10.6
> aiohttp==3.11.13
> python-dotenv==1.0.1
> pyyaml==6.0.2
> alembic==1.15.1
> pytest==8.3.5
> pytest-asyncio==0.25.3
> astroquery==0.4.9
> ```

### 4. Настройте базу данных PostgreSQL

#### 4.1. Запустите PostgreSQL (если не запущен)
Способ зависит от операционной системы. Обычно можно использовать:
```bash
sudo service postgresql start   # Linux
# или через pg_ctl
```

#### 4.2. Создайте пользователя и базу данных
Подключитесь к PostgreSQL под административной учётной записью (обычно `postgres`):
```bash
sudo -u postgres psql
```

Выполните следующие SQL-команды (замените `secure_password` на свой пароль):
```sql
CREATE USER asteroid_user WITH PASSWORD 'secure_password';
CREATE DATABASE asteroid_db OWNER asteroid_user;
GRANT ALL PRIVILEGES ON DATABASE asteroid_db TO asteroid_user;
\q
```

Теперь база данных готова.

### 5. Создайте файл конфигурации

В корне проекта создайте файл `config.yaml`. Скопируйте в него пример настроек:

```yaml
database:
  host: "localhost"
  port: 5432
  user: "asteroid_user"
  password: "secure_password"   # тот же пароль, что вы указали выше
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

> **Примечание**: для работы с публичными API NASA ключ не требуется, но если вы хотите использовать ключ, добавьте поле `api_key` в раздел `nasa_api`.

### 6. Примените миграции базы данных

Проект использует Alembic для управления схемой БД. Выполните:

```bash
alembic upgrade head
```

Если миграции ещё не созданы, можно инициализировать базу вручную с помощью скрипта `create_db.sh` (если он есть). Но лучше использовать Alembic.

### 7. Запустите приложение

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

После запуска API будет доступно по адресу: [http://localhost:8000](http://localhost:8000)

Автоматическая документация (Swagger) откроется по адресу: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🐳 Запуск с помощью Docker (альтернативный способ)

Если вы предпочитаете Docker, можно использовать готовый `docker-compose.yml`:

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

Затем выполните:
```bash
docker-compose up -d
```

---

## ⚙️ Конфигурация

Все настройки хранятся в файле `config.yaml` (или могут быть заданы переменными окружения). Основные параметры:

| Раздел | Поле | Описание |
|--------|------|----------|
| `database` | `host`, `port`, `user`, `password`, `db_name` | Параметры подключения к PostgreSQL |
| `nasa_api` | `base_url` | Базовый URL NASA API |
| | `timeout` | Таймаут запросов (сек) |
| | `retry_attempts` | Количество повторных попыток при сбое |
| | `cad_timeout` | Таймаут для CAD API |
| | `sentry_timeout` | Таймаут для Sentry API |
| `application` | `environment` | Окружение (`development`/`production`) |
| | `log_level` | Уровень логирования (`DEBUG`, `INFO` и т.д.) |
| | `debug` | Включить режим отладки |

---

## 📡 Использование API

Все эндпоинты возвращают данные в формате JSON. Ниже приведены основные группы.

### 🪨 Астероиды (`/asteroids`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/asteroids/near-earth` | Список околоземных астероидов (PHA) |
| GET | `/asteroids/all` | Все астероиды (с пагинацией) |
| GET | `/asteroids/orbit-class/{class}` | Астероиды заданного класса орбиты (Apollo, Aten, Amor) |
| GET | `/asteroids/accurate-diameter` | Астероиды с точно измеренным диаметром |
| GET | `/asteroids/statistics` | Статистика по астероидам |
| GET | `/asteroids/{designation}` | Детальная информация об астероиде (включая сближения и угрозу) |

### 🌍 Сближения (`/approaches`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/approaches/upcoming` | Ближайшие по времени сближения |
| GET | `/approaches/closest` | Самые близкие по расстоянию |
| GET | `/approaches/fastest` | Сближения с наибольшей скоростью |
| GET | `/approaches/in-period` | Сближения за заданный период (с фильтром по расстоянию) |
| GET | `/approaches/statistics` | Статистика по сближениям |
| GET | `/approaches/by-id/{asteroid_id}` | Все сближения астероида по ID |
| GET | `/approaches/by-designation/{designation}` | Все сближения астероида по обозначению |

### ⚠️ Угрозы (`/threats`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/threats/current` | Текущие угрозы (с ненулевым риском) |
| GET | `/threats/high-risk` | Угрозы высокого риска (Туринская шкала ≥ 5) |
| GET | `/threats/by-probability` | Фильтр по вероятности столкновения |
| GET | `/threats/by-energy` | Фильтр по энергии воздействия (Мт) |
| GET | `/threats/statistics` | Статистика по угрозам |
| GET | `/threats/{designation}` | Угроза для конкретного астероида |
| GET | `/threats/by-category/{category}` | Угрозы по категории (локальный, региональный, глобальный) |

> Все эндпоинты поддерживают параметры пагинации `skip` и `limit` (по умолчанию `limit=100`).

---

## 📚 Примеры запросов

**Получить ближайшие 5 сближений:**
```bash
curl "http://localhost:8000/approaches/upcoming?limit=5"
```

**Найти астероид по обозначению (например, 433 Эрос):**
```bash
curl "http://localhost:8000/asteroids/433"
```

**Получить угрозы с Туринской шкалой ≥ 2:**
```bash
curl "http://localhost:8000/threats/current?min_ts=2"
```

Более подробные примеры можно найти в [examples.md](docs/examples.md).

---

## 📁 Структура проекта (основные директории)

```
asteroid-watch/
├── api/                   # FastAPI роутеры и зависимости
├── domains/               # Доменные модули (asteroid, approach, threat)
│   ├── asteroid/          # Модели, схемы, репозитории, сервисы
│   ├── approach/          # ... аналогично
│   └── threat/            # ...
├── shared/                # Общие компоненты
│   ├── config/            # Управление конфигурацией
│   ├── database/          # Подключение к БД
│   ├── external_api/      # Клиенты NASA API
│   ├── infrastructure/    # Базовые классы (репозитории, схемы)
│   ├── resilience/        # Механизмы отказоустойчивости
│   ├── transaction/       # Unit of Work
│   └── utils/             # Вспомогательные утилиты
├── migrations/            # Миграции Alembic
├── tests/                 # Тесты (unit, integration)
├── docs/                  # Дополнительная документация
├── config.yaml            # Файл конфигурации (создаётся пользователем)
├── requirements.txt       # Зависимости
└── README.md              # Этот файл
```

---

## 🧪 Тестирование

Для запуска тестов выполните:

```bash
pytest
```

Для проверки покрытия:

```bash
pytest --cov=. --cov-report=html
```

---

## 🌐 Обновление данных

Проект включает скрипты для ручного обновления данных из NASA API. Пример:

```bash
python scripts/update_data.py
```

Для автоматического ежедневного обновления можно настроить cron (Linux/macOS) или планировщик задач (Windows).

---

## 🤝 Вклад в проект

Проект учебный, но если вы хотите предложить улучшения, создавайте issue или pull request.

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле LICENSE.

---

## 📞 Контакты

Автор: [Ваше имя]  
GitHub: [@your-github](https://github.com/your-github)  
Email: your.email@example.com

---

**Приятного использования Asteroid Watch!** 🚀
