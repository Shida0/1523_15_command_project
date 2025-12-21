"""
Клиент для получения данных о сближениях через CAD API.
Использует Selenium и прямые запросы к NASA API.
"""
import json
import logging
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Union
import requests
from enum import Enum

from .get_date import GetDate

logger = logging.getLogger(__name__)


class CADErrorCode(Enum):
    """Коды ошибок для CAD API"""
    NETWORK_ERROR = "CAD001"
    JSON_PARSE_ERROR = "CAD002"
    DATE_PARSE_ERROR = "CAD003" 
    SELENIUM_ERROR = "CAD004"
    API_ERROR = "CAD005"
    DATA_PARSE_ERROR = "CAD006"
    CONFIG_ERROR = "CAD007"
    VALIDATION_ERROR = "CAD008"


class CADError(Exception):
    """Кастомное исключение для ошибок CAD API"""
    def __init__(self, code: CADErrorCode, message: str, details: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")


class CADURLBuilder:
    """Класс для построения URL запросов к CAD API"""
    
    CAD_BASE_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
    
    @staticmethod
    def build_url(date_min: str, date_max: str, max_distance_au: float) -> str:
        """
        Строит URL для CAD API.
        
        Args:
            date_min: Минимальная дата в формате YYYY-MM-DD
            date_max: Максимальная дата в формате YYYY-MM-DD или +D
            max_distance_au: Максимальное расстояние в AU
            
        Returns:
            Полный URL строкой
            
        Raises:
            CADError: При ошибке валидации параметров
        """
        try:
            params = {
                'date-min': date_min,
                'date-max': date_max,
                'dist-max': str(max_distance_au),
                'body': 'Earth',
                'sort': 'dist',
                'fullname': 'true'
            }
            
            # Валидация параметров
            if not re.match(r'\d{4}-\d{2}-\d{2}', date_min):
                raise CADError(
                    CADErrorCode.VALIDATION_ERROR,
                    f"Неверный формат date-min: {date_min}",
                    {"date_min": date_min}
                )
            
            if not (re.match(r'\d{4}-\d{2}-\d{2}', date_max) or re.match(r'\+\d+', date_max)):
                raise CADError(
                    CADErrorCode.VALIDATION_ERROR,
                    f"Неверный формат date-max: {date_max}",
                    {"date_max": date_max}
                )
            
            if max_distance_au <= 0:
                raise CADError(
                    CADErrorCode.VALIDATION_ERROR,
                    f"max_distance_au должен быть положительным: {max_distance_au}",
                    {"max_distance_au": max_distance_au}
                )
            
            params_str = '&'.join([f'{k}={v}' for k, v in params.items() if v])
            return f"{CADURLBuilder.CAD_BASE_URL}?{params_str}"
            
        except Exception as e:
            raise CADError(
                CADErrorCode.CONFIG_ERROR,
                f"Ошибка построения URL: {str(e)}",
                {"date_min": date_min, "date_max": date_max, "max_distance_au": max_distance_au}
            ) from e


class CADJSONExtractor:
    """Класс для извлечения JSON данных из различных источников"""
    
    @staticmethod
    def extract_from_page(page_source: str) -> Optional[str]:
        """
        Извлекает JSON из исходного кода страницы.
        
        Args:
            page_source: Исходный код страницы
            
        Returns:
            JSON строка или None если не найдено
            
        Raises:
            CADError: При критической ошибке извлечения
        """
        try:
            patterns = [
                r'\{[^{}]*"fields"[^{}]*"data"[^{}]*\}',
                r'<pre[^>]*>([^<]*)</pre>',
                r'<code[^>]*>([^<]*)</code>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    json_text = match.strip()
                    
                    # Если нашли в теге
                    if '<' in json_text:
                        json_text = re.sub(r'<[^>]+>', '', json_text)
                    
                    # Проверяем, что это JSON
                    if json_text.startswith('{') and '"fields"' in json_text and '"data"' in json_text:
                        json_text = json_text.replace('&quot;', '"').replace('&amp;', '&')
                        return json_text
            
            # Ищем любой JSON на странице
            try:
                start = page_source.find('{')
                end = page_source.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_text = page_source[start:end]
                    if '"fields"' in json_text and '"data"' in json_text:
                        return json_text
            except Exception as e:
                logger.debug(f"Ошибка при поиске JSON по позициям: {str(e)}")
                
            return None
            
        except Exception as e:
            raise CADError(
                CADErrorCode.JSON_PARSE_ERROR,
                f"Ошибка извлечения JSON из страницы: {str(e)}",
                {"page_source_length": len(page_source)}
            ) from e


class CADDataParser(GetDate):
    """Класс для парсинга и обработки данных CAD API"""
    
    @staticmethod
    def _extract_numeric_ids_from_name(asteroid_name: str) -> Set[str]:
        """Извлекает все числовые ID из имени астероида"""
        return set(re.findall(r'\b(\d+)\b', asteroid_name))
    
    def process_cad_response(
        self,
        cad_data: Dict, 
        filter_ids: Optional[Set[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Обрабатывает данные из CAD API и преобразует в формат для CloseApproach.
        
        Args:
            cad_data: Данные от CAD API
            filter_ids: Множество ID для фильтрации (уже преобразовано в множество)
            
        Returns:
            Словарь с данными о сближениях
            
        Raises:
            CADError: При ошибке обработки данных
        """
        try:
            results = {}
            
            if 'data' not in cad_data or not cad_data['data']:
                logger.warning("Нет данных в ответе CAD API")
                return results
            
            # Получаем индексы полей
            fields = cad_data.get('fields', [])
            try:
                field_indices = {
                    'des': fields.index('des'),
                    'cd': fields.index('cd'),
                    'dist': fields.index('dist'),
                    'v_rel': fields.index('v_rel'),
                    'fullname': fields.index('fullname') if 'fullname' in fields else -1
                }
            except ValueError as e:
                raise CADError(
                    CADErrorCode.DATA_PARSE_ERROR,
                    f"Неожиданная структура полей: {str(e)}",
                    {"fields": fields, "error": str(e)}
                ) from e
            
            # Уже передано как множество, просто используем
            filter_set = filter_ids
            
            # Предварительно вычисляем числовые ID для фильтрации
            numeric_filter_ids = None
            if filter_set:
                numeric_filter_ids = {ast_id for ast_id in filter_set if ast_id.isdigit()}
            
            for i, entry in enumerate(cad_data['data']):
                try:
                    des = str(entry[field_indices['des']])
                    cd_str = str(entry[field_indices['cd']])
                    distance_au = float(entry[field_indices['dist']])
                    velocity_km_s = float(entry[field_indices['v_rel']])
                    
                    # Получаем имя астероида
                    if field_indices['fullname'] != -1 and field_indices['fullname'] < len(entry):
                        asteroid_name = str(entry[field_indices['fullname']])
                    else:
                        asteroid_name = des
                    
                    # Парсим дату и время
                    try:
                        # Используем метод из родительского класса GetDate
                        approach_time = self._parse_cad_date_exact(cd_str)
                    except ValueError as e:
                        raise CADError(
                            CADErrorCode.DATE_PARSE_ERROR,
                            f"Не удалось распарсить дату '{cd_str}': {str(e)}",
                            {"date_string": cd_str}
                        ) from e
                    
                    # Фильтрация по asteroid_ids если нужно
                    if filter_set and des not in filter_set:
                        # Быстрая проверка с использованием множеств
                        should_skip = True
                        
                        # 1. Проверяем прямое совпадение
                        if des in filter_set:
                            should_skip = False
                        # 2. Проверяем числовые ID в имени
                        elif numeric_filter_ids:
                            # Извлекаем числа из имени астероида
                            numbers_in_name = CADDataParser._extract_numeric_ids_from_name(asteroid_name)
                            # Проверяем пересечение множеств
                            if numeric_filter_ids.intersection(numbers_in_name):
                                should_skip = False
                        
                        if should_skip:
                            continue
                    
                    # Создаем запись в формате для CloseApproach
                    approach_record = {
                        'approach_time': approach_time,
                        'distance_au': distance_au,
                        'distance_km': distance_au * 149597870.7,
                        'velocity_km_s': velocity_km_s,
                        'asteroid_number': des,
                        'asteroid_name': asteroid_name,
                        'data_source': 'NASA CAD API'
                    }
                    
                    # Добавляем в результаты
                    if des not in results:
                        results[des] = []
                    results[des].append(approach_record)
                    
                except (IndexError, ValueError, TypeError) as e:
                    error_details = {
                        "entry_index": i,
                        "entry": entry,
                        "field_indices": field_indices,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                    logger.warning(
                        f"[{CADErrorCode.DATA_PARSE_ERROR.value}] "
                        f"Ошибка обработки записи: {str(e)}",
                        extra=error_details
                    )
                    continue
            
            logger.info(
                f"Обработано {len(results)} уникальных астероидов, "
                f"всего {sum(len(v) for v in results.values())} сближений"
            )
            return results
            
        except Exception as e:
            raise CADError(
                CADErrorCode.DATA_PARSE_ERROR,
                f"Критическая ошибка обработки данных CAD API: {str(e)}",
                {"cad_data_keys": list(cad_data.keys()) if isinstance(cad_data, dict) else str(type(cad_data))}
            ) from e


class CADClient:
    """Основной клиент для получения данных о сближениях"""
    
    def __init__(self, request_delay: float = 3.0):
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        self.url_builder = CADURLBuilder()
        self.json_extractor = CADJSONExtractor()
        self.data_parser = CADDataParser()
        logger.info("CAD Client инициализирован")
    
    def get_close_approaches(
        self,
        asteroid_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_distance_au: float = 0.05
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получает сближения через Selenium или прямой запрос.
        
        Args:
            asteroid_ids: Список ID астероидов для фильтрации
            start_date: Начальная дата
            end_date: Конечная дата
            max_distance_au: Максимальное расстояние в AU
            
        Returns:
            Данные о сближениях
            
        Raises:
            CADError: При критической ошибке получения данных
        """
        try:
            # Устанавливаем даты по умолчанию
            if start_date is None:
                start_date = datetime.now()
            if end_date is None:
                end_date = start_date + timedelta(days=3650)
                
            logger.info(
                f"Получение сближений за период {start_date.strftime('%Y-%m-%d')} - "
                f"{end_date.strftime('%Y-%m-%d')}"
            )
            
            # Форматируем даты для URL
            date_min = start_date.strftime('%Y-%m-%d')
            date_max = end_date.strftime('%Y-%m-%d')
            
            # Преобразуем список ID в множество ОДИН РАЗ здесь
            asteroid_set = set(asteroid_ids) if asteroid_ids else None
            
            # 1. Пробуем прямой запрос
            logger.info("Пробуем прямой запрос к CAD API...")
            direct_data = self._try_direct_request_variants(date_min, date_max, max_distance_au)
            
            if direct_data:
                logger.info(f"Прямой запрос успешен, получено {direct_data.get('count', 0)} записей")
                # Передаем уже преобразованное множество
                return self.data_parser.process_cad_response(direct_data, asteroid_set)
            
            # 2. Если прямой запрос не сработал, пробуем Selenium
            logger.info("Прямой запрос не сработал, пробуем Selenium...")
            try:
                selenium_data = self._try_selenium_request(date_min, date_max, max_distance_au)
                if selenium_data:
                    logger.info(f"Selenium запрос успешен, получено {selenium_data.get('count', 0)} записей")
                    # Передаем уже преобразованное множество
                    return self.data_parser.process_cad_response(selenium_data, asteroid_set)
            except Exception as e:
                raise CADError(
                    CADErrorCode.SELENIUM_ERROR,
                    f"Ошибка Selenium: {str(e)}",
                    {"date_min": date_min, "date_max": date_max, "max_distance_au": max_distance_au}
                ) from e
            
            # 3. Если оба метода не сработали
            raise CADError(
                CADErrorCode.API_ERROR,
                "Не удалось получить данные ни одним из методов",
                {
                    "methods_tried": ["direct_request", "selenium"],
                    "date_min": date_min,
                    "date_max": date_max
                }
            )
            
        except CADError:
            raise  # Пробрасываем уже созданные CADError
        except Exception as e:
            raise CADError(
                CADErrorCode.API_ERROR,
                f"Непредвиденная ошибка при получении сближений: {str(e)}",
                {
                    "asteroid_ids_count": len(asteroid_ids) if asteroid_ids else 0,
                    "start_date": str(start_date),
                    "end_date": str(end_date)
                }
            ) from e
    
    def _try_direct_request_variants(
        self, 
        date_min: str, 
        date_max: str, 
        max_distance_au: float
    ) -> Optional[Dict]:
        """
        Прямой запрос к API с разными вариантами параметров.
        
        Returns:
            Данные от API или None при ошибке
        """
        try:
            # Вычисляем разницу в днях для формата +D
            start_dt = datetime.strptime(date_min, '%Y-%m-%d')
            end_dt = datetime.strptime(date_max, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days
            
            date_variants = [
                date_max,  # Конкретная дата
                f"+{days_diff}",  # Формат +D
            ]
            
            for date_max_variant in date_variants:
                try:
                    url = self.url_builder.build_url(date_min, date_max_variant, max_distance_au)
                    logger.debug(f"Прямой запрос с date-max={date_max_variant}")
                    
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'data' in data and data.get('count', 0) > 0:
                        return data
                    else:
                        logger.debug(f"Пустой ответ для date-max={date_max_variant}")
                        
                except requests.exceptions.RequestException as e:
                    logger.debug(
                        f"[{CADErrorCode.NETWORK_ERROR.value}] "
                        f"Сетевая ошибка для date-max={date_max_variant}: {str(e)}"
                    )
                except json.JSONDecodeError as e:
                    logger.debug(
                        f"[{CADErrorCode.JSON_PARSE_ERROR.value}] "
                        f"Ошибка парсинга JSON для date-max={date_max_variant}: {str(e)}"
                    )
                except Exception as e:
                    logger.debug(
                        f"Ошибка для date-max={date_max_variant}: {str(e)}"
                    )
                    
        except ValueError as e:
            logger.error(
                f"[{CADErrorCode.DATE_PARSE_ERROR.value}] "
                f"Ошибка вычисления дат: {str(e)}",
                extra={"date_min": date_min, "date_max": date_max}
            )
        except Exception as e:
            logger.error(
                f"[{CADErrorCode.API_ERROR.value}] "
                f"Ошибка прямого запроса: {str(e)}",
                extra={"date_min": date_min, "date_max": date_max, "max_distance_au": max_distance_au}
            )
        
        return None
    
    def _try_selenium_request(
        self, 
        date_min: str, 
        date_max: str, 
        max_distance_au: float
    ) -> Optional[Dict]:
        """
        Получает данные через Selenium.
        
        Returns:
            Данные от API через Selenium или None при ошибке
        """
        try:
            # Импортируем Selenium
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Настройка Chrome
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Опции для избежания обнаружения
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Случайный User-Agent
            import random
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            logger.info("Запуск Chrome с Selenium...")
            
            # Пробуем разные способы инициализации драйвера
            driver = None
            
            # Способ 1: Прямое использование Chrome
            try:
                driver = webdriver.Chrome(options=options)
                logger.info("Используем системный ChromeDriver")
            except Exception as e:
                logger.warning(
                    f"[{CADErrorCode.SELENIUM_ERROR.value}] "
                    f"Не удалось запустить системный Chrome: {str(e)}"
                )
                # Способ 2: Попробуем с webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Используем webdriver-manager для ChromeDriver")
                except Exception as e2:
                    raise CADError(
                        CADErrorCode.SELENIUM_ERROR,
                        f"Не удалось запустить Chrome даже с webdriver-manager: {str(e2)}",
                        {"first_error": str(e), "second_error": str(e2)}
                    ) from e2
            
            if not driver:
                return None
            
            try:
                # Формируем URL
                url = self.url_builder.build_url(date_min, date_max, max_distance_au)
                logger.info(f"Загружаем страницу: {url}")
                
                driver.get(url)
                time.sleep(5)  # Увеличиваем время ожидания для Selenium
                
                # Получаем содержимое страницы
                page_source = driver.page_source
                
                # Извлекаем JSON
                json_text = self.json_extractor.extract_from_page(page_source)
                
                if json_text:
                    data = json.loads(json_text)
                    if 'data' in data and data.get('count', 0) > 0:
                        return data
                    else:
                        logger.warning("Selenium вернул пустые данные")
                else:
                    logger.warning("Не удалось найти JSON на странице")
                    
            finally:
                try:
                    driver.quit()
                    logger.info("Chrome драйвер закрыт")
                except Exception as e:
                    logger.warning(f"Ошибка при закрытии драйвера: {str(e)}")
                
        except ImportError as e:
            raise CADError(
                CADErrorCode.SELENIUM_ERROR,
                f"Selenium не установлен: {str(e)}",
                {"package": "selenium"}
            ) from e
        except Exception as e:
            raise CADError(
                CADErrorCode.SELENIUM_ERROR,
                f"Критическая ошибка в Selenium: {str(e)}",
                {"date_min": date_min, "date_max": date_max, "max_distance_au": max_distance_au}
            ) from e
        
        return None

    