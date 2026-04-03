# 🌌 Asteroid Watch

**Asteroid Watch** — система мониторинга потенциально опасных астероидов (PHA). Собирает данные из открытых API NASA, анализирует их и предоставляет REST API + веб-интерфейс для доступа к информации об астероидах, сближениях с Землёй и оценках угроз столкновения.

Проект построен на паттернах DDD, Repository, Unit of Work с использованием FastAPI, SQLAlchemy и PostgreSQL.

---

## ✨ Возможности

- **Данные из NASA API**:
  - SBDB Query API — PHA астероиды (орбита, размер, альбедо, класс)
  - CAD API — сближения с Землёй на 10 лет вперёд
  - Sentry API — оценки рисков (Туринская и Палермская шкалы)
- **PostgreSQL** с асинхронной SQLAlchemy
- **REST API v1** с пагинацией и фильтрацией
- **Веб-интерфейс** (Vanilla JS) — таблицы астероидов, сближений, угроз, детальная страница астероида
- **Автоматическое обновление данных** через `run_update.py`
- **Отказоустойчивость**: retry, circuit breaker, bulkhead, timeout

---

## 🛠 Технологический стек

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy (async)
- PostgreSQL
- aiohttp
- Pydantic
- Alembic

---

## 📋 Предварительные требования

- Python 3.11+
- PostgreSQL 12+
- pip + venv

---

## 🚀 Установка и запуск

### 1. Клонирование и окружение

```bash
git clone https://github.com/your-username/asteroid-watch.git
cd asteroid-watch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. База данных

**Скрипт (Linux/macOS):**
```bash
chmod +x create_db.sh
./create_db.sh
```

**Вручную (все платформы):**
```bash
sudo -u postgres psql
```
```sql
CREATE USER administrator WITH PASSWORD 'secure_password';
CREATE DATABASE asteroid_watch_db ENCODING 'UTF8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE asteroid_watch_db TO administrator;
\c asteroid_watch_db
GRANT ALL ON SCHEMA public TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO administrator;
\q
```

### 3. Файл `.env`

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=administrator
DB_PASSWORD=secure_password
DB_NAME=asteroid_watch_db
CONFIG_PATH=./config.yaml
```

### 4. Миграции

```bash
alembic upgrade head
```

### 5. Запуск API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### 6. Загрузка данных

```bash
python3 run_update.py
```

### 7. Веб-интерфейс

Откройте `frontend/index/index.html` в браузере.

---

## 📡 API Endpoints

Версия: **v1** (`/api/v1`)

### Астероиды

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/asteroids/all` | Все астероиды (пагинация: `skip`, `limit`) |
| GET | `/asteroids/count` | Общее количество |
| GET | `/asteroids/near-earth` | Околоземные (MOID ≤ 0.05 а.е.) |
| GET | `/asteroids/orbit-class/{class}` | По классу орбиты |
| GET | `/asteroids/accurate-diameter` | С измеренным диаметром |
| GET | `/asteroids/statistics` | Статистика |
| GET | `/asteroids/{designation}` | Детали + сближения + угроза |

### Сближения

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/approaches/upcoming` | Ближайшие по времени |
| GET | `/approaches/closest` | Самые близкие |
| GET | `/approaches/fastest` | Наибольшая скорость |
| GET | `/approaches/in-period` | За период |
| GET | `/approaches/statistics` | Статистика |
| GET | `/approaches/count` | Общее количество |
| GET | `/approaches/by-id/{id}` | По ID астероида |
| GET | `/approaches/by-designation/{des}` | По обозначению |

### Угрозы

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/threats/current` | Текущие угрозы (`min_ts`) |
| GET | `/threats/high-risk` | Высокий риск (TS ≥ 5) |
| GET | `/threats/by-probability` | По вероятности |
| GET | `/threats/by-energy` | По энергии |
| GET | `/threats/statistics` | Статистика |
| GET | `/threats/{designation}` | Угроза для астероида |
| GET | `/threats/by-category/{cat}` | По категории |

---

## 📁 Структура проекта

```
asteroid-watch/
├── api/                          # FastAPI роутеры
│   ├── asteroid_api.py
│   ├── approach_api.py
│   └── threat_api.py
│
├── domains/                      # Бизнес-домены (DDD)
│   ├── asteroid/                 # Модели, схемы, репозитории, сервисы
│   ├── approach/
│   └── threat/
│
├── shared/                       # Общие компоненты
│   ├── config/                   # Конфигурация
│   ├── database/                 # SQLAlchemy движок
│   ├── external_api/             # NASA API клиенты (SBDB, CAD, Sentry)
│   ├── infrastructure/           # Базовые репозитории, схемы, сервисы
│   ├── resilience/               # Circuit breaker, bulkhead, timeout
│   ├── transaction/              # Unit of Work
│   └── utils/                    # Утилиты, обработка ошибок
│
├── frontend/                     # Веб-интерфейс (Vanilla JS)
│   ├── index/                    # Главная страница
│   ├── asteroids/                # Каталог астероидов
│   ├── asteroid_detail/          # Детали астероида
│   ├── approaches/               # Сближения
│   ├── threats/                  # Угрозы
│   ├── api.js                    # API клиент
│   ├── main.js
│   └── main.css
│
├── migrations/                   # Alembic миграции
├── main.py                       # Точка входа
├── run_update.py                 # Скрипт обновления данных
├── create_db.sh                  # Создание БД
├── config.yaml
├── .env.example
└── requirements.txt
```

---

## 🌐 Обновление данных

```bash
python3 run_update.py
```

**Процесс:**
1. SBDB Query API → все PHA астероиды (`sb-group=pha`, один запрос, лимит 5000)
2. CAD API → сближения на 10 лет вперёд
3. Sentry API → оценки угроз
4. Данные сохраняются/обновляются в БД
5. Старые записи удаляются (прошлые сближения, отсутствующие в NASA)

**Логи:** `update_log.log` + консоль

**Автоматизация (cron):**
```bash
0 2 * * * cd /path/to/asteroid-watch && venv/bin/python run_update.py >> update_log.log 2>&1
```

---

## 🔧 Миграции

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1
alembic current
```

---

## 📄 Лицензия

MIT

---

**Asteroid Watch** 🚀
