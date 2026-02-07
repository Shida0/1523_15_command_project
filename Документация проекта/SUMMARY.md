# 🌌 **СВОДКА ДОКУМЕНТАЦИИ ASTEROID WATCH**

## 📚 **СТРУКТУРА ДОКУМЕНТАЦИИ**

Этот проект документации состоит из следующих файлов:

| Файл | Назначение |
|------|------------|
| [README.md](README.md) | Главная страница документации |
| [overview.md](overview.md) | Обзор проекта, архитектура и стек технологий |
| [asteroid_domain.md](asteroid_domain.md) | Полное описание домена астероидов |
| [approach_domain.md](approach_domain.md) | Полное описание домена сближений |
| [threat_domain.md](threat_domain.md) | Полное описание домена угроз |
| [shared_components.md](shared_components.md) | Общие компоненты: конфигурация, база данных, внешние API |
| [infrastructure.md](infrastructure.md) | Инфраструктурные компоненты: репозитории, схемы, транзакции |
| [examples.md](examples.md) | Практические примеры использования всех компонентов |
| [testing.md](testing.md) | Стратегия тестирования и структура тестов |
| [deployment.md](deployment.md) | Настройка и развертывание приложения |
| [SUMMARY.md](SUMMARY.md) | Текущий файл - сводка документации |

## 🧩 **АРХИТЕКТУРНЫЕ КОМПОНЕНТЫ**

### **Доменные модули:**
- **asteroid** - управление информацией об астероидах
- **approach** - управление данными о сближениях
- **threat** - управление оценками угроз

### **Общие компоненты:**
- **config** - централизованное управление конфигурацией
- **database** - асинхронные сессии и подключения
- **external_api** - клиенты для взаимодействия с NASA API
- **infrastructure** - базовые классы и интерфейсы
- **resilience** - механизмы отказоустойчивости
- **transaction** - управление транзакциями
- **utils** - вспомогательные утилиты и декораторы

## 🔄 **РАБОЧИЕ ПРОЦЕССЫ**

### **Основные потоки данных:**
1. **Данные астероидов** → NASA SBDB API → `NASASBDBClient` → `AsteroidRepository` → База данных
2. **Данные сближений** → NASA CAD API → `CADClient` → `ApproachRepository` → База данных  
3. **Данные угроз** → NASA Sentry API → `SentryClient` → `ThreatRepository` → База данных

### **Использование UnitOfWork:**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async with UnitOfWork(AsyncSessionLocal) as uow:
    # Работа с репозиториями в рамках одной транзакции
    asteroid = await uow.asteroid_repo.get_by_designation("433")
    approaches = await uow.approach_repo.get_by_asteroid(asteroid.id)
    threat = await uow.threat_repo.get_by_asteroid_id(asteroid.id)
    
    # Все изменения будут зафиксированы вместе при выходе из блока
    await uow.commit()
```

## 🧪 **ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ**

### **Получение астероида по обозначению:**
```python
from domains.asteroid.services.asteroid_service import AsteroidService
from shared.database.engine import AsyncSessionLocal

service = AsteroidService(AsyncSessionLocal)
asteroid = await service.get_by_designation("433")
if asteroid:
    print(f"Найден астероид: {asteroid['name']}")
```

### **Получение ближайших сближений:**
```python
from domains.approach.services.approach_service import ApproachService
from shared.database.engine import AsyncSessionLocal

service = ApproachService(AsyncSessionLocal)
upcoming = await service.get_upcoming(10)
print(f"Ближайшие сближения: {len(upcoming)}")
```

### **Получение угроз высокого риска:**
```python
from domains.threat.services.threat_service import ThreatService
from shared.database.engine import AsyncSessionLocal

service = ThreatService(AsyncSessionLocal)
high_risk = await service.get_high_risk(20)
print(f"Угрозы высокого риска: {len(high_risk)}")
```

## 🚀 **РАЗВЕРТЫВАНИЕ**

Для развертывания приложения:

1. Установите зависимости: `pip install -r requirements.txt`
2. Настройте конфигурацию в `config.yaml`
3. Создайте базу данных PostgreSQL
4. Запустите миграции: `alembic upgrade head`
5. Запустите приложение: `uvicorn main:app --host 0.0.0.0 --port 8000`

## 📊 **ТЕСТИРОВАНИЕ**

Запуск тестов:
```bash
# Все тесты
pytest

# Только модульные
pytest tests/unit/

# Только интеграционные
pytest tests/integration/

# С покрытием
pytest --cov=. --cov-report=html
```

---

**Документация проекта Asteroid Watch завершена.** Все компоненты системы документированы с практическими примерами использования.