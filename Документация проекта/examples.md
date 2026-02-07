# 📚 **ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ**

## 📋 **ОБЗОР**

В этом разделе представлены практические примеры использования всех компонентов системы Asteroid Watch. Примеры демонстрируют реальные сценарии работы с каждым модулем и доменом.

## 🪨 **ПРИМЕРЫ РАБОТЫ С ДОМЕНОМ АСТЕРОИДОВ**

### **1. Получение астероида по обозначению**
```python
from domains.asteroid.services.asteroid_service import AsteroidService
from shared.database.engine import AsyncSessionLocal

async def get_asteroid_by_designation_example():
    service = AsteroidService(AsyncSessionLocal)
    asteroid = await service.get_by_designation("433")  # Астероид Эрос
    
    if asteroid:
        print(f"Найден астероид: {asteroid['name']}")
        print(f"Обозначение: {asteroid['designation']}")
        print(f"Диаметр: {asteroid['estimated_diameter_km']} км")
        print(f"MOID: {asteroid['earth_moid_au']} а.е.")
    else:
        print("Астероид не найден")
```

### **2. Поиск астероидов с высоким риском (MOID < 0.05 а.е.)**
```python
from domains.asteroid.services.asteroid_service import AsteroidService
from shared.database.engine import AsyncSessionLocal

async def get_high_risk_asteroids_example():
    service = AsteroidService(AsyncSessionLocal)
    risky_asteroids = await service.get_by_moid(0.05)
    
    print(f"Найдено {len(risky_asteroids)} потенциально опасных астероидов")
    
    for asteroid in risky_asteroids[:5]:  # Показать первые 5
        print(f"- {asteroid['designation']}: MOID = {asteroid['earth_moid_au']} а.е., "
              f"диаметр = {asteroid['estimated_diameter_km']} км")
```

### **3. Получение астероидов по классу орбиты**
```python
from domains.asteroid.services.asteroid_service import AsteroidService
from shared.database.engine import AsyncSessionLocal

async def get_asteroids_by_orbit_class_example():
    service = AsteroidService(AsyncSessionLocal)
    apollo_asteroids = await service.get_by_orbit_class("Apollo")
    
    print(f"Найдено {len(apollo_asteroids)} астероидов класса Apollo")
    
    for asteroid in apollo_asteroids[:3]:  # Показать первые 3
        print(f"- {asteroid['designation']}: {asteroid['name'] or 'Без имени'}")
```

### **4. Получение статистики по астероидам**
```python
from domains.asteroid.services.asteroid_service import AsteroidService
from shared.database.engine import AsyncSessionLocal

async def get_asteroid_statistics_example():
    service = AsteroidService(AsyncSessionLocal)
    stats = await service.get_statistics()
    
    print("=== Статистика по астероидам ===")
    print(f"Всего астероидов: {stats['total_asteroids']}")
    print(f"Средний диаметр: {stats['average_diameter_km']} км")
    print(f"Минимальный MOID: {stats['min_earth_moid_au']} а.е.")
    print(f"Астероидов с точными диаметрами: {stats['accurate_diameter_count']} "
          f"({stats['percent_accurate']}%)")
    print("Распределение по источнику диаметра:")
    for source, count in stats['diameter_source_stats'].items():
        print(f"  {source}: {count}")
```

### **5. Работа с репозиторием астероидов**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async def asteroid_repository_examples():
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # Получить астероид по обозначению
        asteroid = await uow.asteroid_repo.get_by_designation("433")
        print(f"Астероид: {asteroid.name if asteroid else 'Не найден'}")
        
        # Найти астероиды с точными диаметрами
        accurate_diameter_asteroids = await uow.asteroid_repo.get_asteroids_with_accurate_diameter()
        print(f"Астероидов с точными диаметрами: {len(accurate_diameter_asteroids)}")
        
        # Найти астероиды в диапазоне диаметров
        large_asteroids = await uow.asteroid_repo.get_asteroids_by_diameter_range(
            min_diameter=1.0, max_diameter=10.0
        )
        print(f"Астероидов диаметром 1-10 км: {len(large_asteroids)}")
        
        # Поиск по имени или обозначению
        search_results = await uow.asteroid_repo.search_by_name_or_designation("apophis")
        print(f"Результаты поиска 'apophis': {len(search_results)}")
```

### **6. Создание нового астероида через транзакционный сервис**
```python
from domains.asteroid.services.transactional_asteroid_service import TransactionalAsteroidService

async def create_asteroid_transactionally():
    asteroid_data = {
        "designation": "2023_test_new",
        "name": "Test New Asteroid",
        "absolute_magnitude": 22.0,
        "estimated_diameter_km": 0.05,
        "albedo": 0.15,
        "accurate_diameter": False,
        "diameter_source": "calculated",
        "earth_moid_au": 0.03,
        "perihelion_au": 0.8,
        "aphelion_au": 1.2
    }
    
    created_asteroid = await TransactionalAsteroidService.create_asteroid(asteroid_data)
    
    if created_asteroid:
        print(f"Создан астероид: {created_asteroid['name']} (ID: {created_asteroid['id']})")
        return created_asteroid['id']
    else:
        print("Ошибка создания астероида")
        return None
```

## 🌍 **ПРИМЕРЫ РАБОТЫ С ДОМЕНОМ СБЛИЖЕНИЙ**

### **1. Получение ближайших сближений**
```python
from domains.approach.services.approach_service import ApproachService
from shared.database.engine import AsyncSessionLocal

async def get_upcoming_approaches_example():
    service = ApproachService(AsyncSessionLocal)
    upcoming = await service.get_upcoming(10)
    
    print(f"Ближайшие 10 сближений:")
    for approach in upcoming:
        print(f"- {approach['asteroid_designation']}: {approach['approach_time']}, "
              f"расстояние {approach['distance_au']} а.е., "
              f"скорость {approach['velocity_km_s']} км/с")
```

### **2. Получение самых близких сближений**
```python
from domains.approach.services.approach_service import ApproachService
from shared.database.engine import AsyncSessionLocal

async def get_closest_approaches_example():
    service = ApproachService(AsyncSessionLocal)
    closest = await service.get_closest(5)
    
    print(f"5 самых близких сближений:")
    for approach in closest:
        print(f"- {approach['asteroid_designation']}: {approach['distance_au']} а.е. "
              f"в {approach['approach_time']}")
```

### **3. Получение сближений для конкретного астероида**
```python
from domains.approach.services.approach_service import ApproachService
from shared.database.engine import AsyncSessionLocal

async def get_approaches_by_asteroid_example(asteroid_id: int):
    service = ApproachService(AsyncSessionLocal)
    approaches = await service.get_by_asteroid_id(asteroid_id)
    
    print(f"Сближения для астероида ID {asteroid_id}: {len(approaches)}")
    for approach in approaches:
        print(f"- {approach['approach_time']}: {approach['distance_au']} а.е.")
```

### **4. Работа с репозиторием сближений**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal
from datetime import datetime, timedelta

async def approach_repository_examples():
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # Получить сближения для конкретного астероида
        approaches = await uow.approach_repo.get_by_asteroid(123)
        print(f"Сближения для астероида 123: {len(approaches)}")
        
        # Получить ближайшие сближения
        upcoming = await uow.approach_repo.get_upcoming_approaches(5)
        print(f"Ближайшие сближения: {len(upcoming)}")
        
        # Получить сближения в определенном периоде
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365)
        period_approaches = await uow.approach_repo.get_approaches_in_period(
            start_date, end_date, max_distance=0.05
        )
        print(f"Сближения в течение года: {len(period_approaches)}")
        
        # Получить статистику
        stats = await uow.approach_repo.get_statistics()
        print(f"Всего сближений: {stats['total_approaches']}")
        print(f"Среднее расстояние: {stats['average_distance_au']} а.е.")
```

### **5. Массовое создание сближений**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal
from datetime import datetime, timedelta

async def bulk_create_approaches_example():
    approaches_data = [
        {
            "asteroid_id": 1,
            "approach_time": datetime.now() + timedelta(days=30),
            "distance_au": 0.02,
            "distance_km": 0.02 * 149597870.7,
            "velocity_km_s": 15.5,
            "asteroid_designation": "433",
            "data_source": "NASA CAD API"
        },
        {
            "asteroid_id": 2,
            "approach_time": datetime.now() + timedelta(days=60),
            "distance_au": 0.03,
            "distance_km": 0.03 * 149597870.7,
            "velocity_km_s": 12.0,
            "asteroid_designation": "495",
            "data_source": "NASA CAD API"
        }
    ]
    
    async with UnitOfWork(AsyncSessionLocal) as uow:
        created_count = await uow.approach_repo.bulk_create_approaches(
            approaches_data, 
            calculation_batch_id="batch_2023_12_01"
        )
        print(f"Создано сближений: {created_count}")
```

## ⚠️ **ПРИМЕРЫ РАБОТЫ С ДОМЕНОМ УГРОЗ**

### **1. Получение угроз высокого риска**
```python
from domains.threat.services.threat_service import ThreatService
from shared.database.engine import AsyncSessionLocal

async def get_high_risk_threats_example():
    service = ThreatService(AsyncSessionLocal)
    high_risk = await service.get_high_risk(10)
    
    print(f"Угрозы высокого риска (туринская шкала >= 5): {len(high_risk)}")
    for threat in high_risk:
        print(f"- {threat['designation']}: Шкала Турина = {threat['ts_max']}, "
              f"вероятность = {threat['ip']}, энергия = {threat['energy_megatons']} Мт")
```

### **2. Получение угроз по диапазону риска**
```python
from domains.threat.services.threat_service import ThreatService
from shared.database.engine import AsyncSessionLocal

async def get_threats_by_risk_level_example():
    service = ThreatService(AsyncSessionLocal)
    medium_risk = await service.get_by_risk_level(2, 4)  # Уровень 2-4
    
    print(f"Угрозы среднего риска (2-4): {len(medium_risk)}")
    for threat in medium_risk:
        print(f"- {threat['designation']}: Шкала Турина = {threat['ts_max']}, "
              f"вероятность = {threat['ip']}")
```

### **3. Получение угроз по энергии воздействия**
```python
from domains.threat.services.threat_service import ThreatService
from shared.database.engine import AsyncSessionLocal

async def get_threats_by_energy_example():
    service = ThreatService(AsyncSessionLocal)
    high_energy_threats = await service.get_by_energy(min_energy=100.0, max_energy=1000.0)
    
    print(f"Угрозы с энергией 100-1000 Мт: {len(high_energy_threats)}")
    for threat in high_energy_threats:
        print(f"- {threat['designation']}: Энергия = {threat['energy_megatons']} Мт, "
              f"категория = {threat['impact_category']}")
```

### **4. Работа с репозиторием угроз**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async def threat_repository_examples():
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # Получить угрозу по обозначению
        threat = await uow.threat_repo.get_by_designation("433")
        if threat:
            print(f"Угроза для 433: Шкала Турина = {threat.ts_max}")
        
        # Найти угрозы с высоким риском
        high_risk = await uow.threat_repo.get_high_risk_threats(5)
        print(f"Угроз высокого риска: {len(high_risk)}")
        
        # Найти угрозы по категории воздействия
        regional_threats = await uow.threat_repo.get_threats_by_impact_category("региональный")
        print(f"Региональных угроз: {len(regional_threats)}")
        
        # Получить статистику
        stats = await uow.threat_repo.get_statistics()
        print(f"Всего угроз: {stats['total_threats']}")
        print(f"Угроз высокого риска: {stats['high_risk_count']}")
        print(f"Средняя вероятность: {stats['average_probability']}")
```

### **5. Обновление оценки угрозы**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async def update_threat_assessment_example():
    async with UnitOfWork(AsyncSessionLocal) as uow:
        updated_threat = await uow.threat_repo.update_threat_assessment(
            designation="433",
            new_data={
                "ip": 0.00005,  # Обновленная вероятность
                "ts_max": 0,    # Обновленная шкала Турина
                "energy_megatons": 150.0  # Обновленная энергия
            }
        )
        
        if updated_threat:
            print(f"Оценка угрозы для {updated_threat.designation} обновлена")
            print(f"Новая вероятность: {updated_threat.ip}")
            print(f"Новая шкала Турина: {updated_threat.ts_max}")
        else:
            print("Оценка угрозы не найдена для обновления")
```

## 🌐 **ПРИМЕРЫ РАБОТЫ С ВНЕШНИМИ API**

### **1. Получение данных об астероидах из NASA SBDB**
```python
from shared.external_api.clients.sbdb_api import NASASBDBClient

async def get_asteroids_from_nasa_example():
    async with NASASBDBClient() as client:
        asteroids = await client.get_asteroids(limit=5)
        
        print(f"Получено {len(asteroids)} астероидов из NASA SBDB:")
        for asteroid in asteroids:
            print(f"- {asteroid['designation']}: {asteroid['name'] or 'Без имени'} "
                  f"(диаметр: {asteroid['estimated_diameter_km']} км)")
```

### **2. Получение данных о сближениях из NASA CAD**
```python
from shared.external_api.clients.cad_api import CADClient
from datetime import datetime, timedelta

async def get_approaches_from_nasa_example():
    async with CADClient() as client:
        approaches = await client.get_close_approaches(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
            max_distance_au=0.05
        )
        
        total_approaches = sum(len(v) for v in approaches.values())
        print(f"Получено {total_approaches} сближений из NASA CAD:")
        
        for designation, asteroid_approaches in list(approaches.items())[:3]:
            print(f"Астероид {designation}: {len(asteroid_approaches)} сближений")
            for approach in asteroid_approaches[:2]:  # Показать первые 2
                print(f"  - {approach['approach_time']}: {approach['distance_au']} а.е.")
```

### **3. Получение данных о рисках из NASA Sentry**
```python
from shared.external_api.clients.sentry_api import SentryClient

async def get_threats_from_nasa_example():
    async with SentryClient() as client:
        risks = await client.fetch_current_impact_risks()
        
        print(f"Получено {len(risks)} рисков столкновения из NASA Sentry:")
        for risk in risks[:5]:  # Показать первые 5
            print(f"- {risk.designation}: Шкала Турина = {risk.ts_max}, "
                  f"вероятность = {risk.ip}, энергия = {risk.energy_megatons} Мт")
```

## 🔄 **ПРИМЕРЫ РАБОТЫ С UNIT OF WORK**

### **1. Комплексная транзакция с несколькими доменами**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async def complex_transaction_example():
    async with UnitOfWork(AsyncSessionLocal) as uow:
        try:
            # Создать новый астероид
            new_asteroid = await uow.asteroid_repo.create({
                "designation": "2023_complex_test",
                "name": "Complex Test Asteroid",
                "absolute_magnitude": 20.0,
                "estimated_diameter_km": 0.2,
                "albedo": 0.15,
                "earth_moid_au": 0.04
            })
            
            print(f"Создан астероид: {new_asteroid.id}")
            
            # Создать сближение для этого астероида
            from datetime import datetime
            new_approach = await uow.approach_repo.create({
                "asteroid_id": new_asteroid.id,
                "approach_time": datetime.now() + timedelta(days=180),
                "distance_au": 0.04,
                "distance_km": 0.04 * 149597870.7,
                "velocity_km_s": 14.0,
                "asteroid_designation": new_asteroid.designation,
                "data_source": "Calculated"
            })
            
            print(f"Создано сближение: {new_approach.id}")
            
            # Создать оценку угрозы
            new_threat = await uow.threat_repo.create({
                "asteroid_id": new_asteroid.id,
                "designation": new_asteroid.designation,
                "fullname": new_asteroid.name,
                "ip": 0.0001,
                "ts_max": 1,
                "ps_max": -3.5,
                "diameter": new_asteroid.estimated_diameter_km,
                "v_inf": 14.0,
                "h": new_asteroid.absolute_magnitude,
                "n_imp": 1,
                "impact_years": [2024],
                "last_obs": "2023-01-01",
                "threat_level_ru": "ОЧЕНЬ НИЗКИЙ",
                "torino_scale_ru": "1 — Нормальный (зелёный)",
                "impact_probability_text_ru": "0.01% (1 к 10,000)",
                "energy_megatons": 50.0,
                "impact_category": "локальный",
                "sentry_last_update": datetime.now()
            })
            
            print(f"Создана оценка угрозы: {new_threat.id}")
            
            # Зафиксировать все изменения
            await uow.commit()
            print("Все изменения успешно зафиксированы в одной транзакции")
            
        except Exception as e:
            await uow.rollback()
            print(f"Ошибка в транзакции, изменения откачены: {e}")
```

### **2. Чтение данных из нескольких доменов в одной транзакции**
```python
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal

async def read_from_multiple_domains_example():
    async with UnitOfWork(AsyncSessionLocal) as uow:
        # Получить астероид
        asteroid = await uow.asteroid_repo.get_by_designation("433")
        if not asteroid:
            print("Астероид 433 не найден")
            return
        
        print(f"Астероид: {asteroid.name} (ID: {asteroid.id})")
        print(f"Диаметр: {asteroid.estimated_diameter_km} км")
        print(f"MOID: {asteroid.earth_moid_au} а.е.")
        
        # Получить его сближения
        approaches = await uow.approach_repo.get_by_asteroid(asteroid.id)
        print(f"Сближения: {len(approaches)}")
        for approach in approaches[:3]:  # Показать первые 3
            print(f"  - {approach.approach_time}: {approach.distance_au} а.е.")
        
        # Получить оценку угрозы
        threat = await uow.threat_repo.get_by_asteroid_id(asteroid.id)
        if threat:
            print(f"Угроза: Шкала Турина = {threat.ts_max}, "
                  f"вероятность = {threat.ip}, энергия = {threat.energy_megatons} Мт")
        else:
            print("Оценка угрозы не найдена")
```

## 🛠️ **ПРИМЕРЫ РАБОТЫ С КОНФИГУРАЦИЕЙ**

### **1. Использование глобальной конфигурации**
```python
from shared.config.config_manager import get_config

def config_usage_example():
    config = get_config()
    
    print(f"Окружение: {config.application.environment}")
    print(f"Уровень логирования: {config.application.log_level}")
    print(f"База данных: {config.database.host}:{config.database.port}")
    print(f"URL базы данных: {config.get_database_url()}")
    print(f"Режим production: {config.is_production()}")
```

### **2. Загрузка конфигурации из файла**
```python
from shared.config.config_manager import ConfigManager

def load_config_from_file_example():
    config = ConfigManager().load_from_file('./config.yaml')
    
    print(f"Конфигурация загружена из: {config._loaded_from}")
    print(f"Таймаут SBDB API: {config.nasa_api.sbdb_timeout}")
    print(f"Таймаут CAD API: {config.nasa_api.cad_timeout}")
    print(f"Таймаут Sentry API: {config.nasa_api.sentry_timeout}")
```

## 🧪 **КОМПЛЕКСНЫЙ ПРИМЕР: ПОЛНЫЙ РАБОЧИЙ ПРОЦЕСС**

### **Синхронизация данных из NASA API**
```python
from shared.external_api.clients.sbdb_api import NASASBDBClient
from shared.external_api.clients.cad_api import CADClient
from shared.external_api.clients.sentry_api import SentryClient
from shared.transaction.uow import UnitOfWork
from shared.database.engine import AsyncSessionLocal
from datetime import datetime, timedelta

async def full_sync_process_example():
    """
    Пример полного рабочего процесса синхронизации данных из NASA API
    """
    print("=== НАЧАЛО СИНХРОНИЗАЦИИ ДАННЫХ ИЗ NASA API ===")
    
    # 1. Получить данные об астероидах
    print("\n1. Получение данных об астероидах из NASA SBDB...")
    async with NASASBDBClient() as sbdb_client:
        asteroids_data = await sbdb_client.get_asteroids(limit=10)
        print(f"   Получено {len(asteroids_data)} астероидов")
    
    # 2. Получить данные о сближениях
    print("\n2. Получение данных о сближениях из NASA CAD...")
    async with CADClient() as cad_client:
        approaches_data = await cad_client.get_close_approaches(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
            max_distance_au=0.05
        )
        total_approaches = sum(len(v) for v in approaches_data.values())
        print(f"   Получено {total_approaches} сближений")
    
    # 3. Получить данные о рисках
    print("\n3. Получение данных о рисках из NASA Sentry...")
    async with SentryClient() as sentry_client:
        threats_data = await sentry_client.fetch_current_impact_risks()
        print(f"   Получено {len(threats_data)} рисков столкновения")
    
    # 4. Сохранить все данные в базу данных
    print("\n4. Сохранение данных в базу данных...")
    async with UnitOfWork(AsyncSessionLocal) as uow:
        try:
            # Сохранить астероиды
            created_ast, updated_ast = await uow.asteroid_repo.bulk_create_asteroids(asteroids_data)
            print(f"   Астероиды: создано {created_ast}, обновлено {updated_ast}")
            
            # Сохранить сближения (преобразуем данные в нужный формат)
            all_approaches = []
            for designation, approaches in approaches_data.items():
                for approach in approaches:
                    # Найти ID астероида по обозначению
                    asteroid = await uow.asteroid_repo.get_by_designation(designation)
                    if asteroid:
                        approach['asteroid_id'] = asteroid.id
                        all_approaches.append(approach)
            
            if all_approaches:
                approaches_batch_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                created_app = await uow.approach_repo.bulk_create_approaches(
                    all_approaches, approaches_batch_id
                )
                print(f"   Сближения: создано {created_app}")
            
            # Сохранить угрозы
            threats_to_save = []
            for threat in threats_data:
                # Найти астероид по обозначению
                asteroid = await uow.asteroid_repo.get_by_designation(threat.designation)
                if asteroid:
                    threat_dict = threat.to_dict()
                    threat_dict['asteroid_id'] = asteroid.id
                    threats_to_save.append(threat_dict)
            
            if threats_to_save:
                created_thr, updated_thr = await uow.threat_repo.bulk_create_threats(threats_to_save)
                print(f"   Угрозы: создано {created_thr}, обновлено {updated_thr}")
            
            # Зафиксировать все изменения
            await uow.commit()
            print("\n=== СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО ===")
            
        except Exception as e:
            await uow.rollback()
            print(f"\n=== ОШИБКА СИНХРОНИЗАЦИИ: {e} ===")
            raise

# Запуск примера
# await full_sync_process_example()
```

---

**Следующий раздел:** [ТЕСТИРОВАНИЕ](testing.md) - стратегия тестирования и структура тестов