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

### 4. Настройте базу данных PostgreSQL

#### 4.1. Запустите PostgreSQL (если не запущен)

**Linux:**
```bash
sudo service postgresql start
```

**Windows:**
- PostgreSQL обычно запускается автоматически как служба
- Если нет: Панель управления → Администрирование → Службы → PostgreSQL → Запустить

#### 4.2. Создайте базу данных и пользователя

**Способ А: Использование скрипта `create_db.sh` (Linux/macOS)**

Скрипт `create_db.sh` создаёт базу данных и пользователя с необходимыми правами.

```bash
chmod +x create_db.sh
./create_db.sh
```

> **Важно:** Скрипт требует прав суперпользователя PostgreSQL. Отредактируйте пароль в скрипте перед запуском.

**Способ Б: Ручное создание (все платформы)**

Подключитесь к PostgreSQL под административной учётной записью (обычно `postgres`):

```bash
sudo -u postgres psql
```

Выполните SQL-команды (замените `secure_password` на свой пароль):

```sql
CREATE USER administrator WITH PASSWORD 'secure_password';
CREATE DATABASE asteroid_watch_db
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE asteroid_watch_db TO administrator;
\c asteroid_watch_db
GRANT ALL ON SCHEMA public TO administrator;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO administrator;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO administrator;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO administrator;
\q
```

### 5. Создайте файл окружения `.env`

В корне проекта создайте файл `.env` со следующими переменными:

```bash
# База данных
DB_HOST=localhost
DB_PORT=5432
DB_USER=administrator
DB_PASSWORD=secure_password
DB_NAME=asteroid_watch_db

# Путь к файлу конфигурации (опционально)
CONFIG_PATH=./config.yaml
```

> **Важно:** Все параметры подключения к базе данных (хост, порт, пользователь, пароль, имя БД) берутся **только** из `.env` файла. Файл `config.yaml` используется для дополнительных настроек приложения.

### 6. Настройте файл конфигурации `config.yaml`

Файл `config.yaml` содержит настройки приложения и NASA API (но **не** параметры подключения к БД — они в `.env`).

```yaml
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
  debug: false
  update_interval_minutes: 60
  max_concurrent_updates: 5
  enable_monitoring: true
  monitoring_port: 8000
```

### 7. Примените миграции базы данных

Проект использует Alembic для управления схемой БД:

```bash
alembic upgrade head
```

### 8. Запустите приложение

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

После запуска API будет доступно по адресу: [http://localhost:8000](http://localhost:8000)

Автоматическая документация (Swagger) откроется по адресу: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ⚙️ Конфигурация

### Переменные окружения (`.env`)

Все критические параметры подключения хранятся в файле `.env`:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `DB_HOST` | Хост базы данных | `localhost` |
| `DB_PORT` | Порт базы данных | `5432` |
| `DB_USER` | Пользователь БД | `administrator` |
| `DB_PASSWORD` | Пароль пользователя | `secure_password` |
| `DB_NAME` | Имя базы данных | `asteroid_watch_db` |
| `CONFIG_PATH` | Путь к файлу конфигурации | `./config.yaml` |

### Файл конфигурации (`config.yaml`)

Содержит настройки приложения и NASA API:

| Раздел | Поле | Описание |
|--------|------|----------|
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

Все эндпоинты возвращают данные в формате JSON. API версия: **v1** (префикс `/api/v1`).

### 🪨 Астероиды (`/api/v1/asteroids`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/asteroids/near-earth` | Околоземные астероиды (PHA) с MOID ≤ 0.05 а.е. |
| GET | `/asteroids/all` | **Все астероиды** из базы данных (с пагинацией) |
| GET | `/asteroids/count` | Общее количество астероидов |
| GET | `/asteroids/orbit-class/{orbit_class}` | Астероиды по классу орбиты (Apollo, Aten, Amor) |
| GET | `/asteroids/accurate-diameter` | Астероиды с точно измеренным диаметром |
| GET | `/asteroids/statistics` | Статистика по астероидам |
| GET | `/asteroids/{designation}` | Детальная информация об астероиде + сближения + угроза |

**Параметры запроса:**
- `skip` (int): количество пропускаемых записей (по умолчанию 0)
- `limit` (int): количество возвращаемых записей (по умолчанию все)
- `max_moid` (float): максимальное MOID для фильтрации (только для `/near-earth`)

> **Важно:** Эндпоинт `/asteroids/all` возвращает данные из **вашей базы данных**, а не напрямую из NASA. Для получения данных из NASA используйте скрипт обновления `run_update.py`, который использует **пагинацию NASA API** для получения всех доступных PHA астероидов (без ограничения в 3000 записей).

### 🌍 Сближения (`/api/v1/approaches`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/approaches/upcoming` | Ближайшие по времени сближения |
| GET | `/approaches/closest` | Самые близкие по расстоянию |
| GET | `/approaches/fastest` | Сближения с наибольшей скоростью |
| GET | `/approaches/in-period` | Сближения за заданный период |
| GET | `/approaches/statistics` | Статистика по сближениям |
| GET | `/approaches/count` | Общее количество сближений |
| GET | `/approaches/by-id/{asteroid_id}` | Сближения по ID астероида |
| GET | `/approaches/by-designation/{designation}` | Сближения по обозначению астероида |

**Параметры запроса:**
- `skip` (int): количество пропускаемых записей
- `limit` (int): количество возвращаемых записей
- `start_date` (datetime): начало периода (для `/in-period`)
- `end_date` (datetime): конец периода (для `/in-period`)
- `max_distance` (float): максимальное расстояние в а.е. (для `/in-period`)

### ⚠️ Угрозы (`/api/v1/threats`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/threats/current` | Текущие угрозы с ненулевым риском |
| GET | `/threats/high-risk` | Угрозы высокого риска (Туринская шкала ≥ 5) |
| GET | `/threats/by-probability` | Угрозы по диапазону вероятности |
| GET | `/threats/by-energy` | Угрозы по диапазону энергии воздействия |
| GET | `/threats/statistics` | Статистика по угрозам |
| GET | `/threats/{designation}` | Угроза для конкретного астероида |
| GET | `/threats/by-category/{category}` | Угрозы по категории (локальный, региональный, глобальный) |

**Параметры запроса:**
- `skip` (int): количество пропускаемых записей
- `limit` (int): количество возвращаемых записей
- `min_ts` (int): минимальная Туринская шкала (0-10, для `/current`)
- `min_probability` (float): минимальная вероятность (0.0-1.0)
- `max_probability` (float): максимальная вероятность (0.0-1.0)
- `min_energy` (float): минимальная энергия в Мт
- `max_energy` (float): максимальная энергия в Мт

---

## 📚 Примеры запросов

**Получить ближайшие 5 сближений:**
```bash
curl "http://localhost:8000/api/v1/approaches/upcoming?limit=5"
```

**Найти астероид по обозначению (например, 433 Эрос):**
```bash
curl "http://localhost:8000/api/v1/asteroids/433"
```

**Получить угрозы с Туринской шкалой ≥ 2:**
```bash
curl "http://localhost:8000/api/v1/threats/current?min_ts=2"
```

**Получить статистику по астероидам:**
```bash
curl "http://localhost:8000/api/v1/asteroids/statistics"
```

**Получить сближения за период:**
```bash
curl "http://localhost:8000/api/v1/approaches/in-period?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59"
```

---

## 📁 Подробная структура проекта

```
asteroid-watch/
│
├── 📁 api/                          # Слой API (FastAPI роутеры)
│   ├── __init__.py
│   ├── dependencies.py              # Зависимости для DI (сервисы)
│   ├── asteroid_api.py              # Эндпоинты астероидов
│   ├── approach_api.py              # Эндпоинты сближений
│   └── threat_api.py                # Эндпоинты угроз
│
├── 📁 domains/                      # Бизнес-домены (DDD)
│   ├── __init__.py
│   │
│   ├── 📁 asteroid/                 # Домен астероидов
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── asteroid.py          # SQLAlchemy модель
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── asteroid_schema.py   # Pydantic схемы
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── asteroid_repository.py  # CRUD операции
│   │   └── services/
│   │       ├── __init__.py
│   │       └── asteroid_service.py  # Бизнес-логика
│   │
│   ├── 📁 approach/                 # Домен сближений
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── close_approach.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── approach_schema.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── approach_repository.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── approach_service.py
│   │
│   └── 📁 threat/                   # Домен угроз
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── threat_assessment.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── threat_schema.py
│       ├── repositories/
│       │   ├── __init__.py
│       │   └── threat_repository.py
│       └── services/
│           ├── __init__.py
│           └── threat_service.py
│
├── 📁 shared/                       # Общие компоненты
│   ├── __init__.py
│   │
│   ├── 📁 config/                   # Конфигурация
│   │   ├── __init__.py
│   │   ├── config_manager.py        # Менеджер конфигурации
│   │   └── database_loader.py       # Загрузка настроек БД
│   │
│   ├── 📁 database/                 # База данных
│   │   ├── __init__.py
│   │   ├── engine.py                # SQLAlchemy движок
│   │   └── get_db_config.py         # Получение конфига БД
│   │
│   ├── 📁 external_api/             # Внешние API
│   │   ├── __init__.py
│   │   ├── clients/                 # HTTP клиенты
│   │   │   ├── __init__.py
│   │   │   ├── cad_api.py           # Клиент CAD API
│   │   │   ├── sbdb_api.py          # Клиент SBDB API
│   │   │   └── sentry_api.py        # Клиент Sentry API
│   │   └── wrappers/                # Обёртки API
│   │       ├── __init__.py
│   │       ├── get_approaches.py
│   │       ├── get_data.py
│   │       └── get_threat.py
│   │
│   ├── 📁 infrastructure/           # Инфраструктура
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── base_repository.py   # Базовый репозиторий
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── base_schema.py       # Базовая схема
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── base_service.py      # Базовый сервис
│   │   │   └── update_service.py    # Сервис обновлений
│   │   └── controllers/
│   │       ├── __init__.py
│   │       └── base_controller.py   # Базовый контроллер
│   │
│   ├── 📁 models/                   # Модели
│   │   ├── __init__.py
│   │   └── base.py                  # Базовая модель SQLAlchemy
│   │
│   ├── 📁 resilience/               # Отказоустойчивость
│   │   ├── __init__.py
│   │   ├── bulkhead.py              # Bulkhead паттерн
│   │   ├── circuit_breaker.py       # Circuit Breaker
│   │   └── timeout.py               # Timeout паттерн
│   │
│   ├── 📁 transaction/              # Транзакции
│   │   ├── __init__.py
│   │   ├── coordinator.py           # Координатор транзакций
│   │   └── uow.py                   # Unit of Work
│   │
│   └── 📁 utils/                    # Утилиты
│       ├── __init__.py
│       ├── error_handlers.py        # Обработка ошибок
│       ├── get_date.py              # Парсинг дат
│       └── space_math.py            # Космические расчёты
│
├── 📁 frontend/                     # Фронтенд (Vanilla JS)
│   ├── 📁 index/                    # Главная страница
│   ├── 📁 asteroids/                # Каталог астероидов
│   ├── 📁 asteroid_detail/          # Детали астероида
│   ├── 📁 approaches/               # Сближения
│   ├── 📁 threats/                  # Угрозы
│   ├── api.js                       # API клиент
│   ├── main.js                      # Общие функции
│   └── main.css                     # Общие стили
│
├── 📁 migrations/                   # Миграции Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                    # Версии миграций
│
├── 📁 tests/                        # Тесты
│   ├── __init__.py
│   ├── conftest.py                  # Общие фикстуры
│   │
│   ├── 📁 unit/                     # Юнит-тесты
│   │   ├── __init__.py
│   │   ├── 📁 api/                  # Тесты API
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py          # Фикстуры для API тестов
│   │   │   ├── test_asteroid_api.py
│   │   │   ├── test_approach_api.py
│   │   │   └── test_threat_api.py
│   │   ├── 📁 domains/              # Тесты доменов
│   │   └── 📁 shared/               # Тесты общих компонентов
│   │
│   ├── 📁 integration/              # Интеграционные тесты
│   │   ├── __init__.py
│   │   └── test_*.py
│   │
│   └── 📁 e2e/                      # End-to-End тесты
│       ├── __init__.py
│       └── test_*.py
│
├── 📁 Документация проекта/         # Дополнительная документация
│   ├── 🏗️ Архитектура и структура проекта.md
│   ├── 📖 Рабочий процесс проекта.md
│   └── deployment.md
│
├── 📄 main.py                       # Точка входа (FastAPI app)
├── 📄 run_update.py                 # Скрипт обновления данных
├── 📄 create_db.sh                  # Скрипт создания БД
├── 📄 config.yaml                   # Конфигурация приложения
├── 📄 .env                          # Переменные окружения (БД)
├── 📄 requirements.txt              # Python зависимости
├── 📄 alembic.ini                   # Настройки Alembic
├── 📄 pytest.ini                    # Настройки тестов
├── 📄 setup.py                      # Настройки проекта
└── 📄 README.md                     # Этот файл
```

---

## 🧪 Тестирование

Проект использует **pytest** для тестирования. Тесты разделены на три категории:

### Запуск тестов

**Все тесты:**
```bash
pytest
```

**Все тесты с подробным выводом:**
```bash
pytest -v
```

**Только юнит-тесты:**
```bash
pytest tests/unit/
```

**Только интеграционные тесты:**
```bash
pytest tests/integration/
```

**Конкретный тестовый файл:**
```bash
pytest tests/unit/api/test_asteroid_api.py -v
```

**Конкретный тест:**
```bash
pytest tests/unit/api/test_asteroid_api.py::test_get_all_asteroids -v
```

**С отчётом о покрытии:**
```bash
pytest --cov=. --cov-report=html
```

После выполнения откройте `htmlcov/index.html` в браузере.

**Запуск тестов в несколько процессов:**
```bash
pytest -n auto
```

### Структура тестов

- **Unit-тесты** (`tests/unit/`) — тестируют отдельные компоненты изолированно (моки используются для зависимостей)
- **Integration-тесты** (`tests/integration/`) — тестируют взаимодействие между компонентами (реальная БД)
- **E2E-тесты** (`tests/e2e/`) — тестируют полный цикл работы приложения

### Фикстуры

Проект использует pytest фикстуры для переиспользования кода:
- `client` — тестовый клиент FastAPI
- `mock_asteroid_service` — мок сервиса астероидов
- `mock_approach_service` — мок сервиса сближений
- `mock_threat_service` — мок сервиса угроз

---

## 🌐 Обновление данных

### Ручное обновление

Для обновления данных из NASA API используйте скрипт `run_update.py`:

```bash
python run_update.py
```

**Что происходит:**
1. Запускается `UpdateService`
2. **Запрашиваются данные из SBDB API (астероиды) с пагинацией:**
   - Используется постраничное получение данных (offset/limit)
   - Получаются **ВСЕ** доступные PHA астероиды (без ограничения в 3000)
   - Размер страницы: 1000 записей
   - Автоматическая задержка между запросами для rate limiting
3. Запрашиваются данные из CAD API (сближения)
4. Запрашиваются данные из Sentry API (угрозы)
5. Данные сохраняются в базу данных
6. Выводится отчёт о количестве обновлённых записей

**Логирование:**
- Логи записываются в `update_log.log`
- Логи дублируются в консоль

### Как работает пагинация NASA API

Клиент SBDB использует постраничное получение данных:

```python
# Псевдокод
all_designations = []
offset = 0
batch_size = 1000

while True:
    # Запрашиваем батч данных
    params = {
        'fields': 'pdes',
        'neo': '1',  # Околоземные объекты (PHA фильтруется в БД по MOID)
        'limit': batch_size,
        'offset': offset
    }

    batch = await nasa_api.get(params)
    
    if not batch:
        break  # Достигли конца списка
    
    all_designations.extend(batch)
    offset += batch_size
    
    # Задержка для rate limiting
    await asyncio.sleep(0.5)

# Результат: все PHA астероиды (сейчас ~2,547, будет расти)
```

**Преимущества:**
- ✅ Получение **всех** доступных PHA астероидов
- ✅ Нет ограничения в 3000 записей
- ✅ Автоматическая обработка rate limiting
- ✅ Работает при увеличении количества астероидов

**Текущая статистика NASA (март 2026):**
- PHA астероидов: ~2,547
- Рост: ~30-50 новых в месяц
- Время полного обновления: ~5-10 минут

### Автоматическое обновление

**Linux/macOS (cron):**

Откройте crontab:
```bash
crontab -e
```

Добавьте строку для ежедневного обновления в 02:00:
```bash
0 2 * * * cd /path/to/asteroid-watch && /path/to/venv/bin/python run_update.py >> update_log.log 2>&1
```

**Windows (Task Scheduler):**

1. Откройте "Планировщик заданий"
2. Создайте задачу:
   - Триггер: Ежедневно, 02:00
   - Действие: Запуск программы
   - Программа: `python.exe`
   - Аргументы: `run_update.py`
   - Рабочая папка: `C:\path\to\asteroid-watch`

---

## 📊 Методы создания базы данных

### Метод 1: Скрипт `create_db.sh` (рекомендуется для Linux/macOS)

**Назначение:** Создание базы данных, пользователя и выдача прав.

**Не является инструментом миграций!** Для миграций используется Alembic.

```bash
chmod +x create_db.sh
./create_db.sh
```

**Что делает скрипт:**
1. Создаёт пользователя `administrator`
2. Создаёт базу данных `asteroid_watch_db`
3. Выдаёт все необходимые права

### Метод 2: Ручное создание через psql

Подходит для всех платформ. См. шаг 4.2 в разделе установки.

### Метод 3: Через pgAdmin (Windows)

1. Откройте pgAdmin
2. Создайте базу данных через GUI
3. Создайте пользователя
4. Выдайте права

---

## 🔧 Миграции базы данных

**Важно:** Миграции управляются через **Alembic**, а не через `create_db.sh`.

**Создать новую миграцию:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Применить миграции:**
```bash
alembic upgrade head
```

**Откатить миграцию:**
```bash
alembic downgrade -1
```

**Проверить статус миграций:**
```bash
alembic current
```

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
