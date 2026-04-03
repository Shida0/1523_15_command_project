# 🚀 Деплой на Windows

> **Для кого:** Члены команды без опыта Python/бэкенда
> **Время настройки:** 30-60 минут (первый запуск)
> **Время запуска:** 2 минуты (последующие разы)

---

## Шаг 1: Скачивание проекта

### Через архив (проще)

1. Открой: https://github.com/Shida0/1523_15_command_project
2. Нажми зелёную кнопку **Code** → **Download ZIP**
3. Распакуй архив в `C:\Projects\asteroid-watch`
   - Нажми правой кнопкой на ZIP → **Извлечь всё...**
   - Укажи путь `C:\Projects\asteroid-watch`

### Через Git

Если установлен Git:

```cmd
git clone https://github.com/Shida0/1523_15_command_project.git C:\Projects\asteroid-watch
```

---

## Шаг 2: Установка Python

Python — язык программирования, на котором написан бэкенд проекта.

### 1. Скачай Python

1. Открой: https://www.python.org/downloads/
2. Нажми жёлтую кнопку **Download Python 3.11.x** (или новее)

### 2. Установи Python

⚠️ **Самый важный момент:** при установке **обязательно** поставь галочку ✅ **"Add Python to PATH"**

Без этой галочки команда `python` не будет работать в терминале.

1. Запусти скачанный установщик
2. **Поставь галочку "Add Python to PATH"** (внизу окна)
3. Нажми **Install Now**
4. Дождись окончания
5. Нажми **Close**

### 3. Проверь установку

1. Нажми `Win + R`
2. Введи `cmd`, нажми Enter
3. Введи:
   ```cmd
   python --version
   ```
4. Должно показать `Python 3.11.x` или новее

**Если ошибка "python не является внутренней или внешней командой":**
- Закрой терминал, открой заново
- Если снова ошибка — переустанови Python с галочкой "Add to PATH"

---

## Шаг 3: Установка PostgreSQL

PostgreSQL — система управления базами данных. В ней хранятся все данные проекта: астероиды, сближения, угрозы.

### 1. Скачай PostgreSQL

1. Открой: https://www.postgresql.org/download/windows/
2. Нажми **"Download the installer"**
3. Выбери версию **15** или **16** (обе подойдут)
4. Скачай `.exe` установщик

### 2. Установи PostgreSQL

1. Запусти скачанный файл (он попросит права администратора — согласись)
2. Нажми **Next** на экране приветствия
3. **Installation Directory** — оставь по умолчанию, нажми **Next**
4. **Select Components** — оставь всё как есть, нажми **Next**
5. **Data Directory** — оставь по умолчанию, нажми **Next**
6. **Password** — придумай пароль для суперпользователя `postgres`
   - ⚠️ **Запомни этот пароль!** Он понадобится позже
   - Например: `postgres123`
7. **Port** — оставь **5432**, нажми **Next**
8. **Locale** — оставь **Default locale**, нажми **Next**
9. Нажми **Next** → начнётся установка (2-5 минут)
10. В конце убери галочку "Launch Stack Builder", нажми **Finish**

### 3. Проверь что PostgreSQL работает

1. Нажми `Win + R`, введи `cmd`, нажми Enter
2. Введи:
   ```cmd
   "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
   ```
   (Если ставил версию 15 — замени `16` на `15`)
3. Введи пароль который задавал при установке
4. Если видишь `postgres=#` — всё работает! ✅
5. Выйди: введи `\q` и нажми Enter

**Если ошибка "psql не является внутренней или внешней командой":**
- Используй полный путь как выше: `"C:\Program Files\PostgreSQL\16\bin\psql.exe"`
- Или добавь путь в PATH:
  1. Нажми `Win + S`, введи "Переменные среды"
  2. Нажми "Переменные среды" → найди `Path` → Изменить
  3. Добавь: `C:\Program Files\PostgreSQL\16\bin`
  4. Перезапусти терминал

### 4. Убедись что служба PostgreSQL запущена

PostgreSQL должен работать как фоновая служба Windows:

1. Нажми `Win + R`, введи `services.msc`, нажми Enter
2. Найди в списке **postgresql-x64-16** (или 15)
3. Статус должен быть **Выполняется** (Running)
4. Тип запуска: **Автоматически**

Если не запущен — нажми правой кнопкой → **Запустить**

---

## Шаг 4: Создание базы данных

Теперь нужно создать базу данных и пользователя для проекта.

### 4.1. Открой psql

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

Введи пароль. Должно появиться `postgres=#`

### 4.2. Выполни SQL команды

Копируй команды по одной (замени `secure_password` на свой пароль):

```sql
CREATE USER administrator WITH PASSWORD 'secure_password';
```

Эта команда создаёт пользователя `administrator` с паролем.

```sql
CREATE DATABASE asteroid_watch_db ENCODING 'UTF8' TEMPLATE template0;
```

Создаёт базу данных `asteroid_watch_db`.

```sql
GRANT ALL PRIVILEGES ON DATABASE asteroid_watch_db TO administrator;
```

Даёт пользователю права на базу данных.

```sql
\c asteroid_watch_db
```

Подключается к созданной базе.

```sql
GRANT ALL ON SCHEMA public TO administrator;
```

Даёт права на схему `public`.

```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO administrator;
```

Даёт права на будущие таблицы и последовательности.

```sql
\q
```

Выход из psql.

### 4.3. Проверь что база создана

1. Открой: https://www.pgadmin.org/download/ (скачай pgAdmin если хочешь графический интерфейс)
2. Или просто проверь через psql:
   ```cmd
   "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U administrator -d asteroid_watch_db
   ```
   Введи пароль `secure_password`. Если подключилось — всё ок ✅

---

## Шаг 5: Настройка проекта

### 5.1. Открой терминал в папке проекта

1. Открой проводник, перейди в `C:\Projects\asteroid-watch`
2. В адресной строке (сверху) введи `cmd` и нажми Enter
3. Откроется терминал с путём к проекту

### 5.2. Создай виртуальное окружение

```cmd
python -m venv venv
```

Это создаст папку `venv` с изолированным Python для проекта.

### 5.3. Активируй виртуальное окружение

```cmd
venv\Scripts\activate
```

В начале строки должно появиться `(venv)`.

### 5.4. Установи зависимости

```cmd
pip install -r requirements.txt
```

Это займёт 2-5 минут. Будут скачиваться и устанавливаться все библиотеки проекта.

### 5.5. Создай файл .env

В той же папке проекта создай файл `.env`:

```cmd
notepad .env
```

Вставь содержимое (замени пароль на свой из Шага 4):

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=administrator
DB_PASSWORD=secure_password
DB_NAME=asteroid_watch_db
CONFIG_PATH=./config.yaml
```

Сохрани (`Ctrl+S`) и закрой Блокнот.

**Что здесь:**
- `DB_HOST`, `DB_PORT` — адрес базы данных (локально)
- `DB_USER`, `DB_PASSWORD` — логин и пароль пользователя БД
- `DB_NAME` — имя базы данных
- `CONFIG_PATH` — путь к файлу конфигурации приложения

### 5.6. Примени миграции базы данных

```cmd
venv/bin/alembic upgrade head
```

**Если ошибка** и `alembic` не найден, используй:
```cmd
python -m alembic upgrade head
```

Это создаст все таблицы в базе данных.

### 5.7. Загрузи данные из NASA

```cmd
python run_update.py
```

Это займёт 5-10 минут. Скрипт скачает данные об астероидах, сближениях и угрозах из NASA API и сохранит в базу.

Логи будут в консоли и в файле `update_log.log`.

---

## Шаг 6: Запуск проекта

### Терминал 1 — Бэкенд (API сервер)

В терминале в папке проекта (с активной `venv`):

```cmd
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Должно появиться:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Это означает что API сервер запущен и работает на порту 8000.

**Не закрывай этот терминал!** Сервер должен работать пока ты пользуешься сайтом.

### Терминал 2 — Фронтенд (веб-сайт)

Открой **новый** терминал (первый не закрывай!):

1. Нажми `Win + R`, введи `cmd`, нажми Enter
2. Перейди в папку фронтенда:
   ```cmd
   cd C:\Projects\asteroid-watch\frontend
   ```
3. Запусти простой веб-сервер:
   ```cmd
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

Когда всё уже настроено, запуск занимает 1 минуту:

```cmd
# Терминал 1 — бэкенд
cd C:\Projects\asteroid-watch
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Терминал 2 — фронтенд
cd C:\Projects\asteroid-watch\frontend
python -m http.server 8080
```

---

## Обновление данных

Данные из NASA обновляются скриптом. Запускай когда хочешь свежие данные:

```cmd
cd C:\Projects\asteroid-watch
venv\Scripts\activate
python run_update.py
```

---

## Частые проблемы

### `python не является внутренней или внешней командой`

- Перезапусти терминал
- Если не помогло — переустанови Python с галочкой "Add to PATH"
- Перезагрузи компьютер

### `ModuleNotFoundError: No module named '...'`

- Убедись что `(venv)` активна (видно в начале строки)
- Если нет — выполни `venv\Scripts\activate`
- Выполни `pip install -r requirements.txt`

### `Connection refused` к базе данных

- Проверь что PostgreSQL запущен:
  - `Win + R` → `services.msc` → найди `postgresql-x64-16` → статус **Выполняется**
- Проверь пароль в `.env` (переменная `DB_PASSWORD`)
- Проверь что база `asteroid_watch_db` существует

### `Port 8000 is already in use`

- Закрой все терминалы с Python
- Открой Диспетчер задач (`Ctrl + Shift + Esc`)
- Найди процессы `Python` и заверши их
- Запусти сервер снова

### `alembic: command not found`

Используй:
```cmd
python -m alembic upgrade head
```

### Данные на сайте не загружаются

- Убедись что бэкенд запущен (терминал 1)
- Открой http://localhost:8000/api/v1/asteroids/all?skip=0&limit=5
- Если видишь JSON с данными — сервер работает
- Обнови страницу сайта (`F5`)

---

## Шпаргалка

| Что | Где |
|-----|-----|
| Проект | `C:\Projects\asteroid-watch` |
| Сайт | http://localhost:8080/index/index.html |
| API документация | http://localhost:8000/docs |
| База данных | localhost:5432 |
| `.env` | Параметры подключения к БД |
| `config.yaml` | Настройки приложения и NASA API |
| Служба PostgreSQL | `services.msc` → `postgresql-x64-16` |
