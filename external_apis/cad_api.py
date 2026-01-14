import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from utils.get_date import GetDate  # Импортируем базовый класс для парсинга дат
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class CADClient(GetDate):
    """Асинхронный клиент для получения данных о сближениях."""
    
    CAD_API_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
    
    def __init__(self, timeout: int = 30):
        """
        Инициализация асинхронного клиента CAD.
        
        Args:
            timeout: Таймаут HTTP-запросов в секундах
        """
        super().__init__()
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )      
    async def get_close_approaches(
        self,
        asteroid_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_distance_au: float = 0.05
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Получает данные о сближениях астероидов с Землей.
        
        Args:
            asteroid_ids: Список ID астероидов для фильтрации (опционально)
            start_date: Начальная дата периода (по умолчанию - сегодня)
            end_date: Конечная дата периода (по умолчанию +10 лет)
            max_distance_au: Максимальное расстояние в а.е. (по умолчанию 0.05)
            
        Returns:
            Словарь {designation: [список сближений]}
            
        Raises:
            RuntimeError: При ошибке получения данных
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте контекстный менеджер.")
            
        try:
            start_date = start_date or datetime.now()
            end_date = end_date or start_date + timedelta(days=3650)
            
            params = {
                'date-min': start_date.strftime('%Y-%m-%d'),
                'date-max': end_date.strftime('%Y-%m-%d'),
                'dist-max': str(max_distance_au),
                'body': 'Earth',
                'sort': 'dist',
                'fullname': 'true'
            }
            
            logger.info(f"Запрос сближений за период {params['date-min']} - {params['date-max']}")
            
            async with self.session.get(self.CAD_API_URL, params=params) as response:
                if response.status == 429:  # Too Many Requests
                    retry_after = response.headers.get('Retry-After', 65)
                    await asyncio.sleep(int(retry_after))
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
                response.raise_for_status()
                data = await response.json()
                
                approaches = await self._process_cad_response(data, asteroid_ids)
                logger.info(f"Получено {len(approaches)} уникальных сближений")
                return approaches
                
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"CAD API endpoint not found: {e}")
                return {}
            elif e.status == 429:
                logger.warning("Rate limit exceeded for CAD API")
                raise  # Для retry декоратора
            else:
                logger.error(f"CAD API error {e.status}: {e}")
                raise
            
    async def _process_cad_response(
        self,
        cad_data: Dict[str, Any],
        filter_ids: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Обрабатывает ответ CAD API и преобразует его в формат сближений."""
        results = {}
        
        if 'data' not in cad_data or not cad_data['data']:
            logger.warning("Нет данных в ответе CAD API")
            return results
            
        fields = cad_data.get('fields', [])
        field_indices = self._extract_field_indices(fields)
        
        filter_set = set(filter_ids) if filter_ids else None
        
        for entry in cad_data['data']:
            try:
                approach_record = self._parse_cad_entry(entry, field_indices, filter_set)
                if approach_record:
                    des = approach_record['asteroid_number']
                    if des not in results:
                        results[des] = []
                    results[des].append(approach_record)
            except (IndexError, ValueError, TypeError) as e:
                logger.warning(f"Ошибка обработки записи сближения: {e}")
                continue
                
        return results
    
    def _extract_field_indices(self, fields: List[str]) -> Dict[str, int]:
        """Извлекает индексы полей из заголовков CAD API."""
        try:
            return {
                'des': fields.index('des'),
                'cd': fields.index('cd'),
                'dist': fields.index('dist'),
                'v_rel': fields.index('v_rel'),
                'fullname': fields.index('fullname') if 'fullname' in fields else -1
            }
        except ValueError as e:
            logger.error(f"Неожиданная структура полей: {e}")
            return {}
    
    def _parse_cad_entry(
        self, 
        entry: List[Any], 
        field_indices: Dict[str, int],
        filter_set: Optional[set]
    ) -> Optional[Dict[str, Any]]:
        """Парсит одну запись сближения из CAD API."""
        des = str(entry[field_indices['des']])
        
        if filter_set and des not in filter_set:
            return None
            
        cd_str = str(entry[field_indices['cd']])
        distance_au = float(entry[field_indices['dist']])
        velocity_km_s = float(entry[field_indices['v_rel']])
        
        asteroid_name = self._extract_asteroid_name(entry, field_indices, des)
        approach_time = self._parse_cad_date_exact(cd_str)
        
        return {
            'approach_time': approach_time,
            'distance_au': distance_au,
            'distance_km': distance_au * 149597870.7,
            'velocity_km_s': velocity_km_s,
            'asteroid_number': des,
            'asteroid_name': asteroid_name,
            'data_source': 'NASA CAD API'
        }
    
    def _extract_asteroid_name(self, entry: List[Any], field_indices: Dict[str, int], default: str) -> str:
        """Извлекает имя астероида из записи CAD."""
        if field_indices['fullname'] != -1 and field_indices['fullname'] < len(entry):
            return str(entry[field_indices['fullname']])
        return default