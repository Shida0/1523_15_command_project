# 🚀 Деплой на Arch Linux

> **Для кого:** Сокомандники на Arch Linux
> **Время настройки:** 15-30 минут

---

## Шаг 1: Установка зависимостей

Установи Python, pip, PostgreSQL и Git:

```bash
sudo pacman -S python python-pip postgresql git
```

Это установит:
- `python` — интерпретатор Python
- `python-pip` — менеджер пакетов Python
- `postgresql` — сервер базы данных
- `git` — система контроля версий

---

## Шаг 2: Настройка PostgreSQL

PostgreSQL — система управления базами данных. В ней хранятся все данные проекта: астероиды, сближения, угрозы.

### 2.1. Инициализация кластера базы данных

Перед первым запуском PostgreSQL нужно инициализировать кластер (создать структуру данных):

```bash
sudo -iu postgres initdb -D /var/lib/postgres/data
```

**Что происходит:**
- `sudo -iu postgres` — переключается на пользователя `postgres` (от его имени работает БД)
- `initdb` — команда инициализации
- `-D /var/lib/postgres/data` — путь к директории данных

Если директория уже существует и не пуста, получишь ошибку. В этом случае:
```bash
sudo rm -rf /var/lib/postgres/data
sudo -iu postgres initdb -D /var/lib/postgres/data
```

### 2.2. Запуск службы PostgreSQL

Включи автозапуск и запусти службу:

```bash
sudo systemctl enable --now postgresql
```

**Что делает:**
- `enable` — PostgreSQL будет запускаться автоматически при загрузке
- `--now` — запустить прямо сейчас

Проверь статус:
```bash
systemctl status postgresql
```

Должно быть `active (running)`. Если нет:
```bash
sudo systemctl start postgresql
```

### 2.3. Проверка подключения

Попробуй подключиться к PostgreSQL:

```bash
sudo -iu postgres psql
```

Если видишь `postgres=#` — всё работает ✅

Выйди:
```
\q
```

### 2.4. Создание пользователя и базы данных

Подключись к PostgreSQL:

```bash
sudo -iu postgres psql
```

Выполни SQL команды по одной (замени `secure_password` на свой пароль):

```sql
CREATE USER administrator WITH PASSWORD 'secure_password';
```

Создаёт пользователя `administrator` с паролем. Этот пользователь будет использоваться приложением для подключения к БД.

```sql
CREATE DATABASE asteroid_watch_db ENCODING 'UTF8' TEMPLATE template0;
```

Создаёт базу данных `asteroid_watch_db` с кодировкой UTF-8.

```sql
GRANT ALL PRIVILEGES ON DATABASE asteroid_watch_db TO administrator;
```

Даёт пользователю `administrator` все права на базу данных.

```sql
\c asteroid_watch_db
```

Подключается к созданной базе (нужно для следующих команд).

```sql
GRANT ALL ON SCHEMA public TO administrator;
```

Даёт права на схему `public` (в ней будут создаваться таблицы).

```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO administrator;
```

Даёт права на будущие таблицы и последовательности (auto-increment ID).

```sql
\q
```

Выход из psql.

### 2.5. Проверка подключения новым пользователем

Проверь что созданный пользователь может подключиться:

```bash
psql -U administrator -d asteroid_watch_db -h localhost
```

Введи пароль `secure_password`. Если подключилось — всё ок ✅

Выйди: `\q`

**Если ошибка "password authentication failed":**
- Проверь что пароль правильный
- Убедись что пользователь создан: `sudo -iu postgres psql -c "\du"`

**Если ошибка "connection refused":**
- Убедись что PostgreSQL запущен: `systemctl status postgresql`

---

## Шаг 3: Клонирование проекта

```bash
git clone https://github.com/Shida0/1523_15_command_project.git
cd 1523_15_command_project
```

---

## Шаг 4: Настройка проекта

### 4.1. Виртуальное окружение

Создай изолированное Python окружение для проекта:

```bash
python -m venv venv
```

Активируй:

```bash
source venv/bin/activate
```

В начале строки должно появиться `(venv)`.

### 4.2. Установка зависимостей

```bash
pip install -r requirements.txt
```

Это займёт 2-5 минут. Скачаются и установятся все библиотеки проекта.

### 4.3. Файл .env

Создай файл `.env` в корне проекта:

```bash
cat > .env << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_USER=administrator
DB_PASSWORD=secure_password
DB_NAME=asteroid_watch_db
CONFIG_PATH=./config.yaml
EOF
```

Замени `secure_password` на пароль который задал в Шаге 2.4.

**Что здесь:**
- `DB_HOST`, `DB_PORT` — адрес базы данных (локально, стандартный порт)
- `DB_USER`, `DB_PASSWORD` — логин и пароль пользователя БД
- `DB_NAME` — имя базы данных
- `CONFIG_PATH` — путь к файлу конфигурации приложения

Проверь что файл создан:
```bash
cat .env
```

### 4.4. Миграции базы данных

Создай таблицы в базе данных:

```bash
venv/bin/alembic upgrade head
```

Или если alembic в PATH:
```bash
alembic upgrade head
```

Это применит все миграции и создаст структуру таблиц.

### 4.5. Загрузка данных из NASA

```bash
venv/bin/python run_update.py
```

Это займёт 5-10 минут. Скрипт скачает данные из NASA API:
- PHA астероиды (~2500 штук)
- Сближения на 10 лет вперёд
- Оценки угроз из Sentry API

Логи будут в консоли и в файле `update_log.log`.

---

## Шаг 5: Запуск проекта

### Терминал 1 — Бэкенд (API сервер)

В папке проекта (с активной `venv`):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Должно появиться:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

API сервер запущен на порту 8000. **Не закрывай этот терминал!**

### Терминал 2 — Фронтенд (веб-сайт)

Открой **новый** терминал (первый не закрывай):

```bash
cd 1523_15_command_project/frontend
python -m http.server 8080
```

Должно появиться:
```
Serving HTTP on 0.0.0.0 port 8080 ...
```

### Открой в браузере

- **Сайт:** http://localhost:8080/index/index.html
- **API документация:** http://localhost:8000/docs

Если сайт открывается и видны данные — всё работает! 🎉

---

## Быстрый запуск (последующие разы)

```bash
# Терминал 1 — бэкенд
cd 1523_15_command_project
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Терминал 2 — фронтенд
cd 1523_15_command_project/frontend
python -m http.server 8080
```

---

## Обновление данных

Данные из NASA обновляются скриптом. Запускай когда хочешь свежие данные:

```bash
cd 1523_15_command_project
source venv/bin/activate
python run_update.py
```

---

## Полезные команды PostgreSQL

### Проверить статус службы
```bash
systemctl status postgresql
```

### Перезапустить службу
```bash
sudo systemctl restart postgresql
```

### Посмотреть логи PostgreSQL
```bash
journalctl -u postgresql -f
```

### Подключиться как postgres
```bash
sudo -iu postgres psql
```

### Подключиться как administrator
```bash
psql -U administrator -d asteroid_watch_db -h localhost
```

### Посмотреть список баз данных
```bash
sudo -iu postgres psql -c "\l"
```

### Посмотреть список пользователей
```bash
sudo -iu postgres psql -c "\du"
```

---

## Частые проблемы

### `postgresql.service not found`

PostgreSQL не установлен или не распознан systemd:

```bash
sudo pacman -S postgresql
sudo systemctl daemon-reload
sudo systemctl enable --now postgresql
```

### `could not connect to server: Connection refused`

PostgreSQL не запущен:

```bash
sudo systemctl start postgresql
systemctl status postgresql
```

### `FATAL: role "administrator" does not exist`

Пользователь не создан. Повтори Шаг 2.4.

### `ModuleNotFoundError: No module named '...'`

- Убедись что `venv` активна: `source venv/bin/activate`
- Переустанови зависимости: `pip install -r requirements.txt`

### `Port 8000 already in use`

Найди и убей процесс:

```bash
lsof -ti:8000 | xargs kill -9
```

Или используй другой порт:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### `alembic: command not found`

Используй полный путь:
```bash
venv/bin/alembic upgrade head
```

### Данные на сайте не загружаются

- Убедись что бэкенд запущен (терминал 1)
- Проверь API: http://localhost:8000/api/v1/asteroids/all?skip=0&limit=5
- Если видишь JSON — сервер работает
- Обнови страницу сайта

---

## Шпаргалка

| Что | Где |
|-----|-----|
| Проект | `~/1523_15_command_project` |
| Сайт | http://localhost:8080/index/index.html |
| API документация | http://localhost:8000/docs |
| База данных | localhost:5432 |
| Лог PostgreSQL | `journalctl -u postgresql` |
| `.env` | Параметры подключения к БД |
| `config.yaml` | Настройки приложения и NASA API |

### Управление PostgreSQL

| Действие | Команда |
|----------|---------|
| Запустить | `sudo systemctl start postgresql` |
| Остановить | `sudo systemctl stop postgresql` |
| Перезапустить | `sudo systemctl restart postgresql` |
| Статус | `systemctl status postgresql` |
| Логи | `journalctl -u postgresql -f` |
