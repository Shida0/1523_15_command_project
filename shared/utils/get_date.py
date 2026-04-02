import locale
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)


class GetDate:
    def _parse_cad_date_exact(self, cd_str: str) -> datetime:
        """ТОЧНЫЙ парсинг даты из поля 'cd' NASA CAD API"""
        if not cd_str or not isinstance(cd_str, str):
            raise ValueError(f"Недопустимая строка даты: {cd_str}")

        cd_str = cd_str.strip()

        if len(cd_str) < 17:
            raise ValueError(f"Строка даты слишком короткая: '{cd_str}'")

        original_locale = locale.getlocale(locale.LC_TIME)

        try:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'C')
            except locale.Error:
                pass

        try:
            try:
                naive_dt = datetime.strptime(cd_str, '%Y-%b-%d %H:%M')
                aware_dt = naive_dt.replace(tzinfo=timezone.utc)
                return aware_dt
            except ValueError:
                alternative_formats = [
                    '%Y-%b-%d %H:%M:%S',
                    '%Y-%B-%d %H:%M',
                    '%Y-%B-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                ]

                for fmt in alternative_formats:
                    try:
                        naive_dt = datetime.strptime(cd_str, fmt)
                        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
                        logger.warning(f"Дата '{cd_str}' распарсена альтернативным форматом: {fmt}")
                        return aware_dt
                    except ValueError:
                        continue

                self._debug_date_string(cd_str)
                recovered_dt = self._recover_date_from_string(cd_str)
                aware_dt = recovered_dt.replace(tzinfo=timezone.utc)
                return aware_dt

        finally:
            try:
                locale.setlocale(locale.LC_TIME, original_locale)
            except:
                pass

    def _debug_date_string(self, cd_str: str) -> None:
        """Детальная диагностика проблемной строки даты"""
        logger.error("=" * 60)
        logger.error("НЕВОЗМОЖНО РАСПАРСИТЬ ДАТУ: '%s'", cd_str)
        logger.error("Длина строки: %d", len(cd_str))
        logger.error("Содержит пробел: %s", ' ' in cd_str)
        logger.error("Содержит дефис: %s", '-' in cd_str)
        logger.error("Содержит двоеточие: %s", ':' in cd_str)

        parts = cd_str.split()
        logger.error("Частей (по пробелу): %d", len(parts))
        for i, part in enumerate(parts):
            logger.error("  Часть %d: '%s'", i, part)

        logger.error("=" * 60)

    def _recover_date_from_string(self, cd_str: str) -> datetime:
        """Попытка восстановить дату из поврежденной строки"""
        try:
            clean_str = ' '.join(cd_str.split())

            year_match = re.search(r'\d{4}', clean_str)
            if not year_match:
                raise ValueError(f"Не найден год в строке: {cd_str}")

            year = int(year_match.group(0))

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
                month_match = re.search(r'-(\d{1,2})-', clean_str)
                if month_match:
                    month = int(month_match.group(1))
                else:
                    raise ValueError(f"Не найден месяц в строке: {cd_str}")

            day_match = re.search(r'-(\d{1,2})\s', clean_str)
            if not day_match:
                day_match = re.search(r'-(\d{1,2})$', clean_str)

            if not day_match:
                raise ValueError(f"Не найден день в строке: {cd_str}")

            day = int(day_match.group(1))

            time_match = re.search(r'(\d{1,2}):(\d{1,2})', clean_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
            else:
                hour = minute = 0

            naive_dt = datetime(year, month, day, hour, minute)
            aware_dt = naive_dt.replace(tzinfo=timezone.utc)

            logger.warning(f"ВОССТАНОВЛЕНА дата из '{cd_str}' -> {aware_dt}")
            return aware_dt

        except Exception as e:
            logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Невозможно восстановить дату из '{cd_str}': {e}")
            raise ValueError(f"Необрабатываемый формат даты: {cd_str}")
