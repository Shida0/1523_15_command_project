"""
Запуск обновления данных с улучшенной обработкой ошибок
"""
import asyncio
import logging
from datetime import datetime
from shared.infrastructure.services.update_service import UpdateService
from shared.database.engine import AsyncSessionLocal

# Настройка подробного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_log.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска обновления данных"""
    start_time = datetime.now()
    logger.info(f"=== ЗАПУСК ОБНОВЛЕНИЯ ДАННЫХ ===")
    logger.info(f"Время начала: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Создаем сервис обновления
        update_service = UpdateService(AsyncSessionLocal)
        
        # Запускаем обновление
        result = await update_service.update_all()
        
        # Выводим отчет
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"=== ОТЧЕТ ОБ ОБНОВЛЕНИИ ===")
        logger.info(f"Время окончания: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Общая продолжительность: {duration:.2f} секунд")
        logger.info(f"Обновлено астероидов: {result.get('asteroids', 0)}")
        logger.info(f"Обновлено сближений: {result.get('approaches', 0)}")
        logger.info(f"Обновлено угроз: {result.get('threats', 0)}")
        logger.info(f"=== ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО ===")
        
    except KeyboardInterrupt:
        logger.warning("Обновление прервано пользователем (Ctrl+C)")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Обновление прервано. Прошло времени: {duration:.2f} секунд")
        
    except Exception as e:
        logger.error(f"Критическая ошибка во время обновления: {e}", exc_info=True)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Обновление завершено с ошибками. Прошло времени: {duration:.2f} секунд")
        
        # Пытаемся получить частичный отчет, если возможно
        try:
            update_service = UpdateService(AsyncSessionLocal)
            # Попробуем получить текущее состояние из БД
            async with AsyncSessionLocal() as session:
                from domains.asteroid.models.asteroid import AsteroidModel
                from sqlalchemy import func
                asteroid_count = await session.scalar(func.count(AsteroidModel.id))
                logger.info(f"Текущее количество астероидов в БД: {asteroid_count}")
        except Exception as db_e:
            logger.error(f"Ошибка при попытке получить статистику из БД: {db_e}")


if __name__ == "__main__":
    asyncio.run(main())