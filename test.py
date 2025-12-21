import logging
import sys
from datetime import datetime
from utils import NASASBDBClient
from utils import get_current_close_approaches

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
def setup_logging():
    # Создаём форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Обработчик для файла
    file_handler = logging.FileHandler(
        f'asteroid_monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # В файл пишем всё
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Ловим ВСЕ сообщения
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Убираем лишние логи от библиотек (по желанию)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('chromedriver').setLevel(logging.WARNING)

# ========== ЗАПУСК ПРОГРАММЫ ==========
if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("НАЧАЛО РАБОТЫ МОНИТОРА АСТЕРОИДОВ")
    logger.info("=" * 60)
    
    try:
        # Получаем данные об астероидах
        logger.info("Этап 1: Получение данных об астероидах PHA...")
        client = NASASBDBClient()
        asteroids = client.get_asteroids()
        
        if not asteroids:
            logger.error("Не удалось получить данные об астероидах!")
            exit(1)
        
        logger.info(f"Получено {len(asteroids)} астероидов PHA")
        
        # Получаем сближения
        logger.info("Этап 2: Получение данных о сближениях...")
        approaches = get_current_close_approaches(
            asteroids,
            days=3650,  # можно изменить
            max_distance_au=0.05
        )
        
        if not approaches:
            logger.warning("Не найдено сближений, удовлетворяющих критериям")
        else:
            logger.info(f"Найдено {len(approaches)} сближений")
            
            # Выводим топ-5 самых близких сближений
            logger.info("Топ-5 ближайших сближений:")
            for i, approach in enumerate(approaches[:5], 1):
                logger.info(f"{i}. {approach['asteroid_name']} - "
                           f"Дата: {approach['approach_time']} - "
                           f"Расстояние: {approach['distance_au']:.6f} а.е. "
                           f"({approach['distance_km']:,.0f} км)")
        
        # Сохраняем результаты
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"approaches_{timestamp}.json", "w", encoding='utf-8') as file:
            json.dump(approaches, file, indent=4, ensure_ascii=False, default=str)
        logger.info(f"Данные о сближениях сохранены в approaches_{timestamp}.json")
        
        with open(f"asteroids_{timestamp}.json", "w", encoding='utf-8') as file:
            json.dump(asteroids, file, indent=4, ensure_ascii=False, default=str)
        logger.info(f"Данные об астероидах сохранены в asteroids_{timestamp}.json")
        
        logger.info("=" * 60)
        logger.info("РАБОТА ЗАВЕРШЕНА УСПЕШНО")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        raise