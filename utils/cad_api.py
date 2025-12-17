"""
Клиент для получения данных о сближениях через CAD API.
Использует Selenium и прямые запросы к NASA API.
"""
import json
import logging
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests

from .get_date import GetDate


logger = logging.getLogger(__name__)

class CombinedCADClient(GetDate):
    """Клиент для получения данных о сближениях"""
    
    CAD_BASE_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
    
    def __init__(self, request_delay: float = 3.0):
        super().__init__()
        
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })
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
        
        Возвращает данные в формате, готовом для модели CloseApproach.
        """
        # Устанавливаем даты по умолчанию
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=3650)
            
        logger.info("Получение сближений за период %s - %s", 
                   start_date.strftime('%Y-%m-%d'), 
                   end_date.strftime('%Y-%m-%d'))
        
        # Форматируем даты для URL
        date_min = start_date.strftime('%Y-%m-%d')
        date_max = end_date.strftime('%Y-%m-%d')
        
        # 1. Пробуем прямой запрос с несколькими вариантами формата дат
        logger.info("Пробуем прямой запрос к CAD API...")
        direct_data = self._try_direct_request_variants(date_min, date_max, max_distance_au)
        
        if direct_data:
            logger.info("Прямой запрос успешен")
            return self._process_cad_data(direct_data, asteroid_ids)
        
        # 2. Если прямой запрос не сработал, пробуем Selenium
        logger.info("Прямой запрос не сработал, пробуем Selenium...")
        try:
            selenium_data = self._try_selenium_request(date_min, date_max, max_distance_au)
            if selenium_data:
                logger.info("Selenium запрос успешен")
                return self._process_cad_data(selenium_data, asteroid_ids)
        except Exception as e:
            logger.error("Ошибка Selenium: %s", e)
        
        # 3. Если оба метода не сработали
        logger.error("Не удалось получить данные ни одним из методов")
        return {}
    
    def _try_direct_request_variants(
        self, 
        date_min: str, 
        date_max: str, 
        max_distance_au: float
    ) -> Optional[Dict]:
        """
        Прямой запрос к API с разными вариантами параметров.
        """
        # Варианты для date-max
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
                    url = self._build_cad_url(date_min, date_max_variant, max_distance_au)
                    logger.debug("Прямой запрос с date-max=%s", date_max_variant)
                    
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and data.get('count', 0) > 0:
                            logger.info("Успешный прямой запрос, получено %s записей", 
                                       data.get('count', 0))
                            return data
                    
                except Exception as e:
                    logger.debug("Ошибка для date-max=%s: %s", date_max_variant, e)
                    continue
                    
        except Exception as e:
            logger.error("Ошибка вычисления дат: %s", e)
        
        return None
    
    def _try_selenium_request(
        self, 
        date_min: str, 
        date_max: str, 
        max_distance_au: float
    ) -> Optional[Dict]:
        """
        Получает данные через Selenium.
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
                logger.warning("Не удалось запустить Chrome: %s", e)
                # Способ 2: Попробуем с webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Используем webdriver-manager для ChromeDriver")
                except Exception as e2:
                    logger.error("Не удалось запустить Chrome даже с webdriver-manager: %s", e2)
                    return None
            
            if not driver:
                return None
            
            try:
                # Формируем URL
                url = self._build_cad_url(date_min, date_max, max_distance_au)
                logger.info("Загружаем страницу: %s", url)
                
                driver.get(url)
                time.sleep(3)  # Ждем загрузки
                
                # Получаем содержимое страницы
                page_source = driver.page_source
                
                # Ищем JSON
                json_text = self._extract_json_from_page(page_source)
                
                if json_text:
                    data = json.loads(json_text)
                    if 'data' in data and data.get('count', 0) > 0:
                        logger.info("Успешно получены данные через Selenium: %s записей", 
                                   data.get('count', 0))
                        return data
                    else:
                        logger.warning("Selenium вернул пустые данные")
                else:
                    logger.warning("Не удалось найти JSON на странице")
                    
            finally:
                try:
                    driver.quit()
                    logger.info("Chrome драйвер закрыт")
                except:
                    pass
                
        except ImportError as e:
            logger.error("Selenium не установлен: %s", e)
            return None
        except Exception as e:
            logger.error("Критическая ошибка в Selenium: %s", e)
            return None
        
        return None
    
    def _build_cad_url(self, date_min: str, date_max: str, max_distance_au: float) -> str:
        """
        Строит URL для CAD API.
        """
        params = {
            'date-min': date_min,
            'date-max': date_max,
            'dist-max': str(max_distance_au),
            'body': 'Earth',
            'sort': 'dist',
            'fullname': 'true'
        }
        
        params_str = '&'.join([f'{k}={v}' for k, v in params.items() if v])
        return f"{self.CAD_BASE_URL}?{params_str}"
    
    def _extract_json_from_page(self, page_source: str) -> Optional[str]:
        """
        Извлекает JSON из исходного кода страницы.
        """
        # Ищем JSON в тексте страницы
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
                    # Удаляем HTML теги если они есть
                    json_text = re.sub(r'<[^>]+>', '', json_text)
                
                # Проверяем, что это JSON
                if json_text.startswith('{') and '"fields"' in json_text and '"data"' in json_text:
                    # Очищаем текст
                    json_text = json_text.replace('&quot;', '"').replace('&amp;', '&')
                    return json_text
        
        # Ищем любой JSON на странице
        try:
            # Ищем начало и конец JSON
            start = page_source.find('{')
            end = page_source.rfind('}') + 1
            
            if start != -1 and end > start:
                json_text = page_source[start:end]
                if '"fields"' in json_text and '"data"' in json_text:
                    return json_text
        except Exception:
            pass
        
        return None
    
    def _process_cad_data(
        self, 
        cad_data: Dict, 
        filter_ids: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Обрабатывает данные из CAD API и преобразует в формат для CloseApproach.
        """
        results = {}
        
        if 'data' not in cad_data or not cad_data['data']:
            logger.warning("Нет данных в ответе CAD API")
            return results
        
        # Получаем индексы полей
        fields = cad_data.get('fields', [])
        try:
            des_idx = fields.index('des')
            cd_idx = fields.index('cd')
            dist_idx = fields.index('dist')
            v_rel_idx = fields.index('v_rel')
            # fullname может отсутствовать
            fullname_idx = fields.index('fullname') if 'fullname' in fields else -1
        except ValueError as e:
            logger.error("Неожиданная структура полей: %s, fields: %s", e, fields)
            return results
        
        for i, entry in enumerate(cad_data['data']):
            try:
                # Извлекаем данные
                des = str(entry[des_idx])
                cd_str = str(entry[cd_idx])
                distance_au = float(entry[dist_idx])
                velocity_km_s = float(entry[v_rel_idx])
                
                # Получаем имя астероида
                if fullname_idx != -1 and fullname_idx < len(entry):
                    asteroid_name = str(entry[fullname_idx])
                else:
                    asteroid_name = des
                
                # Парсим дату и время
                try:
                    # Используем ТОЧНЫЙ парсер
                    approach_time = self._parse_cad_date_exact(cd_str)
                except ValueError as e:
                    logger.error("ТОЧНЫЙ ПАРСЕР: Не удалось распарсить дату '%s': %s", cd_str, e)
                    continue  # Пропускаем запись без даты
                
                # Фильтрация по asteroid_ids если нужно
                if filter_ids:
                    found = False
                    for ast_id in filter_ids:
                        # Прямое совпадение или числовой ID в имени
                        if (des == ast_id or 
                            (ast_id.isdigit() and f"({ast_id})" in asteroid_name) or
                            (ast_id.isdigit() and f" {ast_id} " in f" {asteroid_name} ")):
                            found = True
                            break
                    
                    if not found:
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
                logger.warning("Ошибка обработки записи %s: %s, entry: %s", i, e, entry)
                continue
        
        logger.info("Обработано %s уникальных астероидов, всего %s сближений", 
                   len(results), sum(len(v) for v in results.values()))
        return results

    