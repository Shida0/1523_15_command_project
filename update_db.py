#!/usr/bin/env python3
"""
Скрипт для запуска обновления базы данных астероидов.
Запускается вручную или по расписанию (cron).
"""
import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.engine import AsyncSessionLocal
from services.update_service import DataUpdateService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'update.log', mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Отключаем детальное логирование SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def main():
    """Основная функция обновления."""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ОБНОВЛЕНИЯ БАЗЫ ДАННЫХ АСТЕРОИДОВ")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Создаем сервис с настройкой параллелизма
            update_service = DataUpdateService(max_workers=10)
            
            # Запускаем обновление
            result = await update_service.run_daily_update(session)
            
            # Логируем результат
            if result.get("status") == "success":
                logger.info("✅ ОБНОВЛЕНИЕ УСПЕШНО ЗАВЕРШЕНО")
                logger.info(f"   Длительность: {result['duration_seconds']:.2f} секунд")
                logger.info(f"   Обработано PHA: {result['asteroids']['pha_count']}")
                logger.info(f"   Создано/обновлено астероидов: {result['asteroids']['created']}/{result['asteroids']['updated']}")
                logger.info(f"   Рассчитано сближений: {result['approaches']['calculated']}")
                logger.info(f"   Сохранено сближений: {result['approaches']['saved']}")
                logger.info(f"   Сохранено оценок угроз: {result['approaches']['with_threats']}")
                logger.info(f"   Производительность: {result['performance']['asteroids_per_second']:.2f} аст/сек")
            else:
                logger.error(f"❌ ОШИБКА ОБНОВЛЕНИЯ: {result.get('error', 'Unknown error')}")
                sys.exit(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Обновление прервано пользователем")
            sys.exit(130)
        except Exception as e:
            logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
            sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("🏁 ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
    logger.info("=" * 60)

if __name__ == "__main__":
    # Создаем папку для логов если её нет
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Запускаем асинхронную функцию
    asyncio.run(main())