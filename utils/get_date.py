import locale
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GetDate:
    def _parse_cad_date_exact(self, cd_str: str) -> datetime:
        """
        ТОЧНЫЙ парсинг даты из поля 'cd' NASA CAD API.
        
        Согласно документации:
        - Все даты возвращаются в UTC
        - Формат: 'YYYY-MMM-DD HH:MM' (например, '2029-Apr-13 21:46')
        - MMM: 3-буквенная английская аббревиатура месяца
        - Время всегда в 24-часовом формате
        
        Параметры:
            cd_str: Строка даты из поля 'cd' (например, '2029-Apr-13 21:46')
        
        Возвращает:
            datetime объект в UTC
        
        Исключения:
            ValueError: Если строка не соответствует ожидаемому формату
        """
        # 1. Предварительная очистка и валидация
        if not cd_str or not isinstance(cd_str, str):
            raise ValueError(f"Недопустимая строка даты: {cd_str}")
        
        cd_str = cd_str.strip()
        
        # 2. Проверка минимальной длины (например, "2029-Apr-13 21:46" = 17 символов)
        if len(cd_str) < 17:
            raise ValueError(f"Строка даты слишком короткая: '{cd_str}'")
        
        # 3. Сохраняем оригинальную локаль и временно устанавливаем английскую
        original_locale = locale.getlocale(locale.LC_TIME)
        
        try:
            # Устанавливаем английскую локаль для парсинга английских названий месяцев
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        except locale.Error:
            try:
                # Альтернативный вариант для некоторых систем
                locale.setlocale(locale.LC_TIME, 'C')
            except locale.Error:
                # Если не удалось установить локаль, продолжим с текущей
                pass
        
        try:
            # 4. ОСНОВНОЙ ПАРСИНГ - точный формат из документации NASA
            # Формат: Год-АббрМесяца-День Час:Минута
            try:
                return datetime.strptime(cd_str, '%Y-%b-%d %H:%M')
            except ValueError as e:
                # 5. ДОПОЛНИТЕЛЬНЫЕ ВАРИАНТЫ (на случай незначительных отклонений)
                # Пробуем другие возможные форматы, которые могут встретиться
                alternative_formats = [
                    '%Y-%b-%d %H:%M:%S',      # С секундами: '2029-Apr-13 21:46:30'
                    '%Y-%B-%d %H:%M',         # Полное название месяца: '2029-April-13 21:46'
                    '%Y-%B-%d %H:%M:%S',      # Полное название + секунды
                    '%Y-%m-%d %H:%M',         # Цифровой месяц: '2029-04-13 21:46'
                    '%Y-%m-%d %H:%M:%S',      # Цифровой месяц + секунды
                    '%Y-%m-%dT%H:%M:%S',      # ISO-подобный: '2029-04-13T21:46:30'
                ]
                
                for fmt in alternative_formats:
                    try:
                        dt = datetime.strptime(cd_str, fmt)
                        logger.warning(f"Дата '{cd_str}' распарсена альтернативным форматом: {fmt}")
                        return dt
                    except ValueError:
                        continue
                
                # 6. ДЕТАЛЬНАЯ ДИАГНОСТИКА при неудаче
                self._debug_date_string(cd_str)
                
                # 7. Если все форматы не подошли, пытаемся восстановить
                return self._recover_date_from_string(cd_str)
                
        finally:
            # 8. Восстанавливаем оригинальную локаль
            try:
                locale.setlocale(locale.LC_TIME, original_locale)
            except:
                pass

    def _debug_date_string(self, cd_str: str) -> None:
        """
        Детальная диагностика проблемной строки даты.
        """
        logger.error("=" * 60)
        logger.error("НЕВОЗМОЖНО РАСПАРСИТЬ ДАТУ: '%s'", cd_str)
        logger.error("Длина строки: %d символов", len(cd_str))
        logger.error("Содержит пробел: %s", ' ' in cd_str)
        logger.error("Содержит дефис: %s", '-' in cd_str)
        logger.error("Содержит двоеточие: %s", ':' in cd_str)
        
        # Анализ структуры
        parts = cd_str.split()
        logger.error("Частей (по пробелу): %d", len(parts))
        for i, part in enumerate(parts):
            logger.error("  Часть %d: '%s'", i, part)
        
        logger.error("=" * 60)

    def _recover_date_from_string(self, cd_str: str) -> datetime:
        """
        Попытка восстановить дату из поврежденной или нестандартной строки.
        Используется только в крайнем случае!
        """
        try:
            # Удаляем все лишние пробелы
            clean_str = ' '.join(cd_str.split())
            
            # Извлекаем год (первые 4 цифры)
            import re
            year_match = re.search(r'\d{4}', clean_str)
            if not year_match:
                raise ValueError(f"Не найден год в строке: {cd_str}")
            
            year = int(year_match.group(0))
            
            # Ищем месяц по английским аббревиатурам
            month_abbrs = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            month = None
            for abbr, month_num in month_abbrs.items():
                if abbr in clean_str:
                    month = month_num
                    break
            
            if month is None:
                # Пробуем найти цифру месяца
                month_match = re.search(r'-(\d{1,2})-', clean_str)
                if month_match:
                    month = int(month_match.group(1))
                else:
                    raise ValueError(f"Не найден месяц в строке: {cd_str}")
            
            # Ищем день
            day_match = re.search(r'-(\d{1,2})\s', clean_str)
            if not day_match:
                day_match = re.search(r'-(\d{1,2})$', clean_str)
            
            if not day_match:
                raise ValueError(f"Не найден день в строке: {cd_str}")
            
            day = int(day_match.group(1))
            
            # Ищем время (часы:минуты)
            time_match = re.search(r'(\d{1,2}):(\d{1,2})', clean_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
            else:
                hour = minute = 0
            
            # Создаем datetime с валидацией
            dt = datetime(year, month, day, hour, minute)
            
            logger.warning(f"ВОССТАНОВЛЕНА дата из '{cd_str}' -> {dt}")
            return dt
            
        except Exception as e:
            logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Невозможно восстановить дату из '{cd_str}': {e}")
            raise ValueError(f"Необрабатываемый формат даты: {cd_str}")