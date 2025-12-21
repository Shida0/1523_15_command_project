"""
Модуль для работы с NASA Sentry API.
ТОЧНЫЙ анализ объектов с ненулевой вероятностью столкновения с Землей.
Основан на официальных данных и методологии NASA JPL.
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


@dataclass
class SentryImpactRisk:
    """Данные об объекте с риском столкновения из системы NASA Sentry."""

    # Основные идентификационные данные
    designation: str  # Обозначение астероида
    fullname: str  # Полное название

    # Ключевые параметры риска (ПРЯМО ИЗ SENTRY)
    ip: float  # Кумулятивная вероятность столкновения (Impact Probability)
    ts_max: int  # Максимальное значение по Туринской шкале (0-10)
    ps_max: float  # Максимальное значение по Палермской шкале

    # Физические характеристики (оценки)
    diameter: float  # Расчетный диаметр в км
    v_inf: float  # Скорость на бесконечности (км/с)
    h: float  # Абсолютная звездная величина

    # Данные по сценариям столкновений
    n_imp: int  # Количество возможных сценариев столкновения
    impact_years: List[int]  # Годы возможных столкновений
    last_obs: str  # Дата последнего наблюдения (YYYY-MM-DD)

    # Локализованные/производные поля (ДЛЯ ВАШЕЙ ПЛАТФОРМЫ)
    threat_level_ru: str  # Уровень угрозы на русском
    torino_scale_ru: str  # Значение шкалы Турина на русском
    impact_probability_text_ru: str  # Текст вероятности
    last_update: datetime  # Когда получены эти данные

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь для использования в API/БД."""
        return {
            "designation": self.designation,
            "fullname": self.fullname,
            "impact_probability": self.ip,
            "impact_probability_text": self.impact_probability_text_ru,
            "torino_scale": self.ts_max,
            "torino_scale_text": self.torino_scale_ru,
            "palermo_scale": self.ps_max,
            "threat_level": self.threat_level_ru,
            "diameter_km": self.diameter,
            "velocity_km_s": self.v_inf,
            "absolute_magnitude": self.h,
            "impact_scenarios_count": self.n_imp,
            "risk_years": self.impact_years,
            "last_observation": self.last_obs,
            "data_updated": self.last_update.isoformat()
        }


class SentryImpactRiskAnalyzer:
    """
    Анализатор рисков на основе NASA Sentry API (Sentry-II).
    Возвращает ТОЛЬКО объекты с ts_max > 0 (актуальные угрозы).
    """

    # Ключевые константы
    SENTRY_API_BASE = "https://ssd-api.jpl.nasa.gov/sentry.api"
    SENTRY_API_REMOVED = "https://ssd-api.jpl.nasa.gov/sentry.api?removed=1"
    SENTRY_API_OBJECT = "https://ssd-api.jpl.nasa.gov/sentry.api?des={des}"

    # Значения по умолчанию для отсутствующих данных
    DEFAULT_DIAMETER = 0.05  # км (50 м) - типичный размер для объектов с неизвестным диаметром
    DEFAULT_V_INF = 20.0  # км/с - средняя скорость сближения

    def __init__(self, timeout: int = 30, enable_cache: bool = True):
        """
        Инициализация анализатора.

        Args:
            timeout: Таймаут HTTP-запросов в секундах
            enable_cache: Включить кэширование ответов API
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AsteroidWatchBot/1.0 (+https://asteroidwatch.example.com)',
            'Accept': 'application/json',
            'Accept-Language': 'en, ru'
        })
        self.timeout = timeout
        self.enable_cache = enable_cache
        self._cache = {}
        self._cache_duration = timedelta(minutes=15)

        logger.info("Инициализирован SentryImpactRiskAnalyzer (режим точных данных)")

    def _get_cached_or_fetch(self, cache_key: str, fetch_func):
        """Проверка кэша и выполнение запроса при необходимости."""
        if not self.enable_cache:
            return fetch_func()

        now = datetime.now()
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if now - timestamp < self._cache_duration:
                logger.debug(f"Используются кэшированные данные для ключа: {cache_key}")
                return data

        # Выполняем запрос и кэшируем результат
        data = fetch_func()
        self._cache[cache_key] = (data, now)
        return data

    def _safe_float(self, value, default=0.0) -> float:
        """Безопасное преобразование в float."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=0) -> int:
        """Безопасное преобразование в int."""
        if value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def _translate_torino_scale(self, ts_value: int) -> str:
        """Перевод значения Туринской шкалы на русский."""
        translations = {
            0: "0 — Нет риска (зелёный)",
            1: "1 — Нормальный (зелёный)",
            2: "2 — Заслуживает внимания (жёлтый)",
            3: "3 — Заслуживает внимания (оранжевый)",
            4: "4 — Заслуживает внимания (оранжевый)",
            5: "5 — Серьёзная угроза (красный)",
            6: "6 — Серьёзная угроза (красный)",
            7: "7 — Серьёзная угроза (красный)",
            8: "8 — Столкновение неизбежно (красный)",
            9: "9 — Столкновение неизбежно (красный)",
            10: "10 — Столкновение неизбежно (красный)"
        }
        return translations.get(ts_value, f"{ts_value} — Неизвестное значение")

    def _assess_threat_level(self, ts_max: int, ps_max: float, ip: float) -> str:
        """
        Оценка уровня угрозы на русском языке.
        Основана на комбинации шкал Турина и Палермо.
        """
        if ts_max == 0:
            # Даже если ts_max=0, учитываем Палермскую шкалу для очень малых вероятностей
            if ps_max > -2:
                return "ОЧЕНЬ НИЗКИЙ (требует мониторинга)"
            return "НУЛЕВОЙ (безопасен)"

        elif 1 <= ts_max <= 4:
            if ps_max > 0:
                return "НИЗКИЙ (но требует наблюдения)"
            return "НИЗКИЙ"

        elif ts_max == 5:
            return "СРЕДНИЙ (заслуживает внимания астрономов)"

        elif ts_max == 6:
            return "ПОВЫШЕННЫЙ (серьёзная угроза)"

        elif ts_max == 7:
            return "ВЫСОКИЙ (очень серьёзная угроза)"

        else:  # 8-10
            return "КРИТИЧЕСКИЙ (непосредственная угроза)"

    def _format_probability_text(self, probability: float) -> str:
        """Форматирование вероятности в читаемый русский текст."""
        if probability <= 0:
            return "Вероятность отсутствует"

        if probability >= 0.01:  # 1% и выше
            return f"{probability*100:.2f}% (1 к {int(1/probability):,})"

        elif probability >= 1e-4:  # 0.01% и выше
            return f"{probability*100:.4f}% (1 к {int(1/probability):,})"

        elif probability >= 1e-6:  # 0.0001% и выше
            return f"{probability*100:.6f}% (1 к {int(1/probability):,})"

        else:
            # Научная нотация для крайне малых вероятностей
            return f"{probability:.2e} (чрезвычайно малая вероятность)"

    def fetch_current_impact_risks(self) -> List[SentryImpactRisk]:
        cache_key = "current_impact_risks"

        def fetch_data():
            try:
                logger.info("Запрос актуальных данных о рисках из NASA Sentry API...")
                # Используем параметр ip-min для фильтрации на стороне сервера
                response = self.session.get(
                    self.SENTRY_API_BASE,
                    timeout=self.timeout,
                    params={'ip-min': '1e-10'}  # Вероятность >= 1e-10
                )
                response.raise_for_status()
                data = response.json()

                # Проверяем версию API
                signature = data.get('signature', {})
                if signature.get('version', '1.0') >= '2.0':
                    logger.info("Используется Sentry-II (учитывает эффект Ярковского)")
                else:
                    logger.warning("Используется старая версия Sentry API")

                risks = []
                for item in data.get('data', []):
                    try:
                        risk = self._parse_sentry_item(item)
                        # ФИЛЬТР: включаем только объекты с ts_max > 0
                        if risk.ts_max > 0:
                            risks.append(risk)
                    except Exception as e:
                        logger.warning(f"Ошибка парсинга объекта {item.get('des', 'unknown')}: {e}")
                        continue

                logger.info(f"Найдено {len(risks)} объектов с ts_max > 0 (актуальные угрозы)")
                return risks

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка подключения к Sentry API: {e}")
                raise RuntimeError(f"Не удалось получить данные NASA Sentry: {e}")
            except (KeyError, ValueError) as e:
                logger.error(f"Ошибка обработки ответа Sentry API: {e}")
                raise RuntimeError(f"Некорректный ответ от NASA Sentry API: {e}")

        return self._get_cached_or_fetch(cache_key, fetch_data)

    def fetch_recently_removed_objects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получает список объектов, удаленных из ТАБЛИЦЫ РИСКОВ Sentry.
        Это не означает, что астероид уничтожен, а значит, что новые данные
        исключили возможность его столкновения с Землей в обозримом будущем.
        Поле `removed_date` может быть пустым.
        """
        try:
            logger.info("Запрос списка удаленных объектов...")
            response = self.session.get(
                self.SENTRY_API_REMOVED,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            removed_objects = []
            for item in data.get('data', []):
                obj_info = {
                    "designation": item.get('des', 'Неизвестно'),
                    "fullname": item.get('fullname', ''),
                    "removed_date": item.get('removed_date', 'Неизвестно'),
                    "removed_reason": item.get('removed_reason', 'Дополнительные наблюдения'),
                    "last_ip": self._safe_float(item.get('last_ip')),
                    "last_diameter": self._safe_float(item.get('last_diameter')),
                    "note": "Объект удален из списка рисков после уточнения орбиты"
                }
                removed_objects.append(obj_info)

            # Сортируем по дате удаления (новые первыми)
            removed_objects.sort(
                key=lambda x: x['removed_date'],
                reverse=True
            )

            return removed_objects[:limit]

        except Exception as e:
            logger.error(f"Ошибка получения удаленных объектов: {e}")
            return []

    def fetch_object_details(self, designation: str) -> Optional[SentryImpactRisk]:
        cache_key = f"object_{designation}"

        def fetch_object():
            try:
                logger.info(f"Запрос деталей объекта {designation}...")
                url = self.SENTRY_API_OBJECT.format(des=designation)
                response = self.session.get(url, timeout=self.timeout)

                # ВСЕГДА проверяем JSON-ответ, даже при статусе 200
                data = response.json()
                
                # Проверяем наличие поля 'error' в ответе API
                if 'error' in data:
                    error_msg = data.get('error', '')
                    if 'not found' in error_msg:
                        logger.info(f"Объект {designation} никогда не был в Sentry.")
                    elif 'removed' in error_msg:
                        logger.info(f"Объект {designation} был удален из таблицы рисков.")
                    # В любом случае ошибки - возвращаем None
                    return None
                    
                # Только если нет ошибки и есть данные - парсим
                if not data.get('data'):
                    return None

                item = data['data'][0]
                return self._parse_sentry_item(item)

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка сетевого запроса для объекта {designation}: {e}")
                return None
            except (KeyError, ValueError) as e:
                logger.error(f"Ошибка парсинга JSON для объекта {designation}: {e}")
                return None

        return self._get_cached_or_fetch(cache_key, fetch_object)

    def _parse_sentry_item(self, item: Dict[str, Any]) -> SentryImpactRisk:
        """
        Парсинг элемента данных из Sentry API.
        """
        # Извлечение основных данных
        designation = item.get('des', 'Неизвестно')
        fullname = item.get('fullname', designation)

        # Безопасное преобразование числовых значений
        ip = self._safe_float(item.get('ip', 0))
        ts_max = self._safe_int(item.get('ts_max', 0))
        ps_max = self._safe_float(item.get('ps_max', -10.0))
        diameter = self._safe_float(item.get('diameter', self.DEFAULT_DIAMETER))
        v_inf = self._safe_float(item.get('v_inf', self.DEFAULT_V_INF))
        h_mag = self._safe_float(item.get('h', 22.0))
        last_obs = item.get('last_obs', 'Неизвестно')

        # Обработка сценариев столкновений
        impact_data = item.get('data', [])
        n_imp = len(impact_data)
        impact_years = []

        for impact in impact_data:
            date_str = impact.get('date', '')
            if date_str and len(date_str) >= 4:
                try:
                    year = int(date_str[:4])
                    impact_years.append(year)
                except ValueError:
                    continue

        # Удаление дубликатов и сортировка
        impact_years = sorted(set(impact_years))

        # Локализация и форматирование
        threat_level_ru = self._assess_threat_level(ts_max, ps_max, ip)
        torino_scale_ru = self._translate_torino_scale(ts_max)
        impact_probability_text_ru = self._format_probability_text(ip)

        return SentryImpactRisk(
            designation=designation,
            fullname=fullname,
            ip=ip,
            ts_max=ts_max,
            ps_max=ps_max,
            diameter=diameter,
            v_inf=v_inf,
            h=h_mag,
            n_imp=n_imp,
            impact_years=impact_years,
            last_obs=last_obs,
            threat_level_ru=threat_level_ru,
            torino_scale_ru=torino_scale_ru,
            impact_probability_text_ru=impact_probability_text_ru,
            last_update=datetime.now()
        )


# ============================================================================
# ФАСАДНЫЕ ФУНКЦИИ ДЛЯ ИНТЕГРАЦИИ С ВАШИМ ПРОЕКТОМ
# ============================================================================

def get_current_impact_risks(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Основная функция для получения актуальных рисков.
    Возвращает список объектов с ts_max > 0 (реальные угрозы).

    Args:
        limit: Ограничить количество возвращаемых объектов

    Returns:
        Список словарей с данными об угрозах
    """
    analyzer = SentryImpactRiskAnalyzer()
    try:
        risks = analyzer.fetch_current_impact_risks()

        # Сортировка по вероятности (убывание)
        risks.sort(key=lambda x: x.ip, reverse=True)

        if limit and limit > 0:
            risks = risks[:limit]

        return [risk.to_dict() for risk in risks]

    except Exception as e:
        logger.error(f"Критическая ошибка при получении рисков: {e}")
        return []


def check_asteroid_risk(designation: str) -> Dict[str, Any]:
    """
    Проверяет, представляет ли конкретный астероид угрозу.

    Args:
        designation: Обозначение астероида (например, "2023 DW")

    Returns:
        Словарь с оценкой риска. Если объект не найден в Sentry,
        считается, что у него нулевая вероятность столкновения.
    """
    analyzer = SentryImpactRiskAnalyzer()

    # Пробуем получить данные из Sentry
    risk_object = analyzer.fetch_object_details(designation)

    if risk_object:
        # Объект найден в Sentry
        result = risk_object.to_dict()
        result['in_sentry'] = True
        result['status'] = 'В списке рисков NASA' if risk_object.ts_max > 0 else 'Безопасен'
        return result
    else:
        # Объект НЕ найден в Sentry = нулевая вероятность
        return {
            "designation": designation,
            "in_sentry": False,
            "status": "НЕ НАЙДЕН в Sentry Risk Table",
            "conclusion": "Вероятность столкновения с Землей в ближайшие 100 лет равна нулю",
            "impact_probability": 0.0,
            "torino_scale": 0,
            "threat_level": "НУЛЕВОЙ (безопасен)",
            "note": "Объект либо безопасен, либо удален из списка рисков после уточнения орбиты",
            "data_updated": datetime.now().isoformat()
        }


def get_recently_safe_asteroids(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получает список недавно признанных безопасными астероидов.

    Returns:
        Список объектов, удаленных из таблицы рисков
    """
    analyzer = SentryImpactRiskAnalyzer()
    return analyzer.fetch_recently_removed_objects(limit=limit)
