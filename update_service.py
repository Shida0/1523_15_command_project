# update_service.py
"""
Сервис ежедневного обновления данных об астероидах, сближениях и угрозах.
Собирает данные из NASA API и сохраняет в JSON файлы.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

from utils import get_asteroid_data, get_current_close_approaches, get_all_treats

# Конфигурация путей
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Создание директорий если их нет
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Настройка логирования
def setup_logging():
    """Настраивает логирование с записью в файл и выводом в консоль."""
    log_file = LOGS_DIR / f"asteroid_update_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Хэндлер для записи в файл
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode="w")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Хэндлер для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Инициализация логгера
logger = setup_logging()

def save_json(data: Any, filename: str) -> bool:
    """
    Сохраняет данные в JSON файл.
    
    Args:
        data: Данные для сохранения
        filename: Имя файла (без пути)
        
    Returns:
        True если успешно, False в противном случае
    """
    try:
        filepath = DATA_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Данные сохранены в {filename} ({len(data) if isinstance(data, list) else 'N/A'} записей)")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения данных в {filename}: {e}")
        return False

async def update_asteroids() -> Tuple[List[Dict[str, Any]], bool]:
    """
    Обновляет данные об астероидах.
    
    Returns:
        Кортеж (данные астероидов, успех операции)
    """
    logger.info("Начинаем обновление данных об астероидах...")
    
    try:
        asteroids = await get_asteroid_data()
        
        # ФИКС: Успехом считаем, если получили хоть какие-то данные
        success = len(asteroids) > 0
        
        if not asteroids:
            logger.warning("Не получено данных об астероидах")
            return [], success
            
        save_json(asteroids, "asteroids.json")
        
        # Логируем статистику
        with_names = sum(1 for a in asteroids if a.get('name'))
        accurate_diameters = sum(1 for a in asteroids if a.get('accurate_diameter', False))
        
        logger.info(f"Обновление астероидов завершено:")
        logger.info(f"  Всего астероидов: {len(asteroids)}")
        logger.info(f"  С именами: {with_names}")
        logger.info(f"  С точными диаметрами: {accurate_diameters}")
        
        return asteroids, success
        
    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении астероидов: {e}", exc_info=True)
        return [], False

async def update_approaches(asteroids: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Обновляет данные о сближениях.
    
    Args:
        asteroids: Список астероидов для поиска сближений
        
    Returns:
        Кортеж (данные сближений, успех операции)
    """
    logger.info("Начинаем обновление данных о сближениях...")
    
    try:
        approaches = await get_current_close_approaches(asteroids, days=3650)
        
        if not approaches:
            logger.warning("Не получено данных о сближениях")
            return [], False
            
        # Группируем сближения по годам для статистики
        year_stats = {}
        for approach in approaches:
            year = approach['approach_time'].year
            year_stats[year] = year_stats.get(year, 0) + 1
            
        success = save_json(approaches, "approaches.json")
        
        logger.info(f"Обновление сближений завершено:")
        logger.info(f"  Всего сближений: {len(approaches)}")
        
        # Выводим статистику по годам
        logger.info("  Распределение по годам:")
        for year, count in sorted(year_stats.items()):
            logger.info(f"    {year}: {count} сближений")
            
        return approaches, success
        
    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении сближений: {e}", exc_info=True)
        return [], False

async def update_threats() -> Tuple[List[Dict[str, Any]], bool]:
    """
    Обновляет данные об угрозах.
    
    Returns:
        Кортеж (данные угроз, успех операции)
    """
    logger.info("Начинаем обновление данных об угрозах...")
    
    try:
        threats = await get_all_treats()
        
        if not threats:
            logger.warning("Не получено данных об угрозах")
            return [], False
            
        # Анализируем уровни угроз
        threat_levels = {}
        torino_scales = {}
        
        for threat in threats:
            level = threat.get('threat_level', 'Неизвестно')
            torino = threat.get('torino_scale', 0)
            
            threat_levels[level] = threat_levels.get(level, 0) + 1
            torino_scales[torino] = torino_scales.get(torino, 0) + 1
            
        success = save_json(threats, "threats.json")
        
        logger.info(f"Обновление угроз завершено:")
        logger.info(f"  Всего угроз: {len(threats)}")
        
        # Статистика по уровням угроз
        logger.info("  Распределение по уровням угроз:")
        for level, count in sorted(threat_levels.items()):
            logger.info(f"    {level}: {count}")
            
        # Статистика по шкале Турина
        logger.info("  Распределение по шкале Турина:")
        for scale, count in sorted(torino_scales.items()):
            logger.info(f"    {scale}: {count}")
            
        return threats, success
        
    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении угроз: {e}", exc_info=True)
        return [], False

async def daily_update():
    """
    Выполняет полное ежедневное обновление данных.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"НАЧАЛО ЕЖЕДНЕВНОГО ОБНОВЛЕНИЯ: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    results = {
        'asteroids': {'success': False, 'count': 0},
        'approaches': {'success': False, 'count': 0},
        'threats': {'success': False, 'count': 0}
    }
    
    try:
        # 1. Обновление астероидов
        asteroids, asteroids_success = await update_asteroids()
        results['asteroids']['success'] = asteroids_success
        results['asteroids']['count'] = len(asteroids)
        
        # 2. Обновление сближений (только если есть астероиды)
        if asteroids:
            approaches, approaches_success = await update_approaches(asteroids)
            results['approaches']['success'] = approaches_success
            results['approaches']['count'] = len(approaches)
        else:
            logger.warning("Пропускаем обновление сближений: нет данных об астероидах")
            
        # 3. Обновление угроз
        threats, threats_success = await update_threats()
        results['threats']['success'] = threats_success
        results['threats']['count'] = len(threats)
        
    except Exception as e:
        logger.critical(f"Непредвиденная ошибка в процессе обновления: {e}", exc_info=True)
        
    finally:
        # Подведение итогов
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("ИТОГИ ОБНОВЛЕНИЯ:")
        logger.info(f"  Общее время: {duration}")
        logger.info(f"  Астероиды: {'УСПЕХ' if results['asteroids']['success'] else 'ОШИБКА'} ({results['asteroids']['count']} записей)")
        logger.info(f"  Сближения: {'УСПЕХ' if results['approaches']['success'] else 'ОШИБКА'} ({results['approaches']['count']} записей)")
        logger.info(f"  Угрозы: {'УСПЕХ' if results['threats']['success'] or results['threats']['count'] == 0 else 'ОШИБКА'} ({results['threats']['count']} записей)")
        
        # Статус успешности всего обновления
        total_success = all(r['success'] for r in results.values())
        status = "УСПЕШНО" if total_success else "С ОШИБКАМИ ЛИБО С ПРЕДУПРЕЖДЕНИЯМИ"
        
        logger.info(f"СТАТУС ОБНОВЛЕНИЯ: {status}")
        logger.info(f"ОКОНЧАНИЕ ОБНОВЛЕНИЯ: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Создаем файл метаданных об обновлении
        metadata = {
            'update_timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'results': results,
            'status': status
        }
        
        save_json(metadata, "update_metadata.json")

if __name__ == "__main__":
    """
    Точка входа для запуска сервиса обновления.
    """
    try:
        # Запуск асинхронного обновления
        asyncio.run(daily_update())
    except KeyboardInterrupt:
        logger.info("Обновление прервано пользователем")
    except Exception as e:
        logger.critical(f"Фатальная ошибка при запуске сервиса: {e}", exc_info=True)