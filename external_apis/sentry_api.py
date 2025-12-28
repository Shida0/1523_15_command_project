# sentry_api.py (исправленная версия)
"""
Асинхронный клиент для NASA Sentry API (Sentry-II).
Получает данные об объектах с ненулевой вероятностью столкновения с Землей.
"""
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SentryImpactRisk:
    """Данные об объекте с риском столкновения из системы NASA Sentry."""
    designation: str
    fullname: str
    ip: float
    ts_max: int
    ps_max: float
    diameter: float
    v_inf: float
    h: float
    n_imp: int
    impact_years: List[int]
    last_obs: str
    threat_level_ru: str
    torino_scale_ru: str
    impact_probability_text_ru: str
    last_update: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь."""
        return asdict(self)

class SentryClient:
    """Асинхронный клиент для получения данных о рисках столкновений."""
    
    SENTRY_API_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'AsteroidWatchBot/1.0',
                'Accept': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def fetch_current_impact_risks(self) -> List[SentryImpactRisk]:
        """Получает все актуальные риски столкновений с ts_max > 0."""
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте контекстный менеджер.")
            
        try:
            logger.info("Запрос актуальных данных о рисках из NASA Sentry API...")
            params = {'ip-min': '1e-10'}
            
            async with self.session.get(self.SENTRY_API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Проверяем структуру ответа перед обработкой
                if 'data' not in data:
                    logger.warning("Ответ Sentry API не содержит ключа 'data'")
                    return []
                
                risks = []
                for item in data.get('data', []):
                    try:
                        risk = self._parse_sentry_item(item)
                        if risk.ts_max > 0:
                            risks.append(risk)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Ошибка парсинга объекта {item.get('des', 'N/A')}: {e}. Пропускаем.")
                        continue
                    except Exception as e:
                        logger.error(f"Неожиданная ошибка парсинга: {e}. Пропускаем объект.")
                        continue
                        
                logger.info(f"Найдено {len(risks)} объектов с ts_max > 0")
                return risks
                
        except (aiohttp.ClientError, ValueError) as e:
            logger.error(f"Ошибка получения данных Sentry: {e}")
            raise RuntimeError(f"Не удалось получить данные NASA Sentry: {e}")
            
    async def fetch_object_details(self, designation: str) -> Optional[SentryImpactRisk]:
        """Получает детальную информацию о конкретном объекте."""
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте контекстный менеджер.")
            
        try:
            url = f"{self.SENTRY_API_URL}?des={designation}"
            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.info(f"Объект {designation} не найден в Sentry API.")
                    return None
                    
                response.raise_for_status()
                data = await response.json()
                
                if 'error' in data or not data.get('data'):
                    return None
                
                if data.get('data'):
                    return self._parse_sentry_item(data['data'][0])
                return None
                
        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка при запросе объекта {designation}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе объекта {designation}: {e}")
            return None
            
    def _parse_sentry_item(self, item: Dict[str, Any]) -> SentryImpactRisk:
        """Парсит элемент данных из Sentry API в объект SentryImpactRisk."""
        # Безопасное извлечение данных с правильными типами
        designation = self._safe_extract_str(item, 'des', 'Неизвестно')
        fullname = self._safe_extract_str(item, 'fullname', designation)
        last_obs = self._safe_extract_str(item, 'last_obs', 'Неизвестно')
        
        # Извлечение числовых значений. Сначала пробуем 'max', затем 'cum'[citation:2][citation:4]
        ip = self._safe_extract_float(item, 'ip', 0.0)
        
        ts_max = self._safe_extract_int(item, 'ts_max', 0)
        if ts_max == 0:
            ts_cum = self._safe_extract_int(item, 'ts', 0)  # Попытка получить cumulative
            if ts_cum != 0:
                logger.debug(f"Для объекта {designation} используется ts_cum={ts_cum}, так как ts_max=0")
        
        ps_max = self._safe_extract_float(item, 'ps_max', -10.0)
        if ps_max <= -10.0:  # Значение по умолчанию, возможно поле отсутствует
            ps_cum = self._safe_extract_float(item, 'ps', -10.0)
            if ps_cum > -10.0:
                ps_max = ps_cum
                logger.debug(f"Для объекта {designation} используется ps_cum={ps_cum} как ps_max")
        
        diameter = self._safe_extract_float(item, 'diameter', 0.05)
        v_inf = self._safe_extract_float(item, 'v_inf', 20.0)
        h_mag = self._safe_extract_float(item, 'h', 22.0)
        
        n_imp, impact_years = self._extract_impact_scenarios(item.get('data', []))
        
        # Локализация данных
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
    
    def _safe_extract_str(self, item: Dict, key: str, default: str) -> str:
        """Безопасно извлекает строковое значение из словаря."""
        value = item.get(key, default)
        if value is None:
            return default
        return str(value)
    
    def _safe_extract_float(self, item: Dict, key: str, default: float) -> float:
        """Безопасно извлекает и преобразует значение в float."""
        value = item.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.debug(f"Не удалось преобразовать '{value}' в float для ключа '{key}'. Используется значение по умолчанию {default}.")
            return default
    
    def _safe_extract_int(self, item: Dict, key: str, default: int) -> int:
        """Безопасно извлекает и преобразует значение в int."""
        value = item.get(key)
        if value is None:
            return default
        try:
            return int(float(value))  # Сначала в float, если строка "22.5"
        except (ValueError, TypeError):
            logger.debug(f"Не удалось преобразовать '{value}' в int для ключа '{key}'. Используется значение по умолчанию {default}.")
            return default
    
    def _extract_impact_scenarios(self, impact_data: List[Dict]) -> Tuple[int, List[int]]:
        """Извлекает информацию о сценариях столкновений."""
        impact_years = []
        
        for impact in impact_data:
            date_str = impact.get('date', '')
            if date_str and len(date_str) >= 4:
                try:
                    year = int(date_str[:4])
                    impact_years.append(year)
                except ValueError:
                    continue
        # Удаляем дубликаты и сортируем
        unique_years = sorted(set(impact_years))
        return len(impact_data), unique_years
        
    def _translate_torino_scale(self, ts_value: int) -> str:
        """Переводит значение Туринской шкалы на русский язык."""
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
        """Оценивает уровень угрозы на основе шкал Турина и Палермо.[citation:4]"""
        if ts_max == 0:
            if ps_max < -2:
                return "НУЛЕВОЙ (ниже фонового уровня)"
            else:
                return "ОЧЕНЬ НИЗКИЙ"
        elif 1 <= ts_max <= 4:
            return "НИЗКИЙ (требует наблюдения)"
        elif ts_max == 5:
            return "СРЕДНИЙ (заслуживает внимания астрономов)"
        elif ts_max == 6:
            return "ПОВЫШЕННЫЙ (серьёзная угроза)"
        elif ts_max == 7:
            return "ВЫСОКИЙ (очень серьёзная угроза)"
        elif ts_max >= 8:
            return "КРИТИЧЕСКИЙ (непосредственная угроза)"
        else:
            return "НЕОПРЕДЕЛЕН"
            
    def _format_probability_text(self, probability: float) -> str:
        """Форматирует вероятность в читаемый русский текст."""
        if probability <= 0:
            return "Вероятность отсутствует"
        # Защита от деления на ноль
        if probability > 0:
            try:
                odds = int(1/probability)
                odds_formatted = f"{odds:,}".replace(",", " ")
            except (ZeroDivisionError, ValueError, OverflowError):
                odds_formatted = "очень большое"
        else:
            odds_formatted = "N/A"
            
        if probability >= 0.01:  # 1% и выше
            return f"{probability*100:.2f}% (1 к {odds_formatted})"
        elif probability >= 1e-4:  # 0.01% и выше
            return f"{probability*100:.4f}% (1 к {odds_formatted})"
        elif probability >= 1e-6:  # 0.0001% и выше
            return f"{probability*100:.6f}% (1 к {odds_formatted})"
        else:
            return f"{probability:.2e} (чрезвычайно малая вероятность, 1 к {odds_formatted})"