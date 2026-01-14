import logging
import aiohttp
import asyncio
import traceback
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from utils.space_math import get_size_by_albedo, get_size_by_h_mag

logger = logging.getLogger(__name__)

class NASASBDBClient:
    """Клиент для работы с NASA Small-Body Database."""
    
    SBDB_QUERY_URL = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
    
    def __init__(self, timeout: int = 60, max_workers: int = 10, 
                 batch_size: int = 50, delay_between_batches: float = 1.0):
        self.timeout = timeout
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'AsteroidWatchBot/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)
            
    async def get_asteroids(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Основной метод получения данных об астероидах."""
        if not self.session:
            raise RuntimeError("Сессия не инициализирована")
            
        try:
            logger.info("Получение списка потенциально опасных астероидов...")
            designations = await self._get_pha_list(limit)
            
            if not designations:
                logger.warning("Не получено обозначений PHA")
                return []
                
            logger.info(f"Получено {len(designations)} обозначений")
            logger.info(f"Запрос данных для {len(designations)} астероидов...")
            
            results = []
            failed = 0
            
            for i in range(0, len(designations), self.batch_size):
                batch = designations[i:i + self.batch_size]
                batch_results = await self._process_batch(batch)
                
                for result in batch_results:
                    if isinstance(result, dict):
                        results.append(result)
                    else:
                        failed += 1
                        if failed <= 10:
                            logger.warning(f"Ошибка обработки: {type(result).__name__}")
                
                if i + self.batch_size < len(designations):
                    await asyncio.sleep(self.delay_between_batches)
                    
                processed = min(i + self.batch_size, len(designations))
                logger.info(f"Обработано {processed}/{len(designations)} астероидов")
            
            self._log_diameter_statistics(results)
            logger.info(f"Успешно получено {len(results)} астероидов, не удалось: {failed}")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка получения астероидов: {e}\n{traceback.format_exc()}")
            return []
    
    async def _process_batch(self, batch: List[str]) -> List:
        """Обрабатывает батч астероидов."""
        tasks = [
            asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._fetch_with_astroquery,
                des
            )
            for des in batch
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка конкретных ошибок NASA
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                if "rate limit" in str(result).lower():
                    await asyncio.sleep(65)  # Ждем чуть больше минуты
                    # Повторяем запрос для этого астероида
                    try:
                        retry_result = await asyncio.get_event_loop().run_in_executor(
                            self.executor, self._fetch_with_astroquery, batch[i]
                        )
                        batch_results[i] = retry_result
                    except:
                        batch_results[i] = self._create_fallback_asteroid(batch[i])
        
        processed_results = []
        
        for des, result in zip(batch, batch_results):
            if isinstance(result, dict):
                processed_results.append(result)
            elif isinstance(result, Exception) or result is None:
                processed_results.append(self._create_fallback_asteroid(des))
            else:
                processed_results.append(None)
        
        return processed_results
    
    def _fetch_with_astroquery(self, designation: str) -> Optional[Dict[str, Any]]:
        """Синхронный запрос через astroquery для одного астероида."""
        try:
            from astroquery.jplsbdb import SBDB
            
            try:
                result = SBDB.query(designation, phys=True, full_precision=True)
            except Exception:
                result = SBDB.query(designation, full_precision=False)
            
            if not result or 'object' not in result:
                return None
            
            return self._parse_astroquery_result(result, designation)
            
        except Exception as e:
            logger.error(f"Astroquery ошибка для {designation}: {e}")
            return None

    def _parse_astroquery_result(self, data: Dict, designation: str) -> Dict[str, Any]:
        """Парсит результат astroquery в формат AsteroidModel."""
        try:
            obj = data.get('object', {})
            orbit = data.get('orbit', {})
            phys_par = data.get('phys_par', {})
            
            name = self._extract_asteroid_name(obj.get('fullname', ''))
            perihelion_au, aphelion_au = self._extract_orbital_elements(orbit)
            earth_moid_au = self._extract_earth_moid(orbit)
            
            h_mag = self._extract_absolute_magnitude(phys_par, obj, designation)
            albedo, has_albedo_data = self._extract_albedo(phys_par, obj)
            diameter_km, diameter_source, accurate_diameter = self._extract_diameter(
                phys_par, obj, h_mag, albedo, has_albedo_data
            )
            
            orbit_class_info = obj.get('orbit_class', {})
            orbit_class = orbit_class_info.get('name', '') if orbit_class_info else ''
            
            return {
                'designation': designation,
                'name': name,
                'perihelion_au': perihelion_au,
                'aphelion_au': aphelion_au,
                'earth_moid_au': earth_moid_au,
                'absolute_magnitude': h_mag,
                'estimated_diameter_km': diameter_km,
                'accurate_diameter': accurate_diameter,
                'albedo': albedo,
                'orbit_class': orbit_class,
                'orbit_id': orbit.get('orbit_id'),
                'diameter_source': diameter_source,
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга astroquery для {designation}: {e}")
            return self._create_fallback_asteroid(designation)
    
    def _extract_asteroid_name(self, fullname: str) -> Optional[str]:
        """Извлекает имя астероида из полного названия."""
        if not fullname:
            return None
            
        parts = fullname.split('(')
        if len(parts) > 1:
            name_part = parts[0].strip()
            if name_part and not name_part.replace(' ', '').isdigit():
                return name_part
        return None
    
    def _extract_orbital_elements(self, orbit: Dict) -> tuple:
        """Извлекает перигелий и афелий из орбитальных данных."""
        def find_value(key: str):
            elements = orbit.get('elements', {})
            if isinstance(elements, dict):
                return self._extract_astro_value(elements.get(key))
            elif isinstance(elements, list):
                for elem in elements:
                    if isinstance(elem, dict) and elem.get('name') == key:
                        return self._extract_astro_value(elem.get('value'))
            return self._extract_astro_value(orbit.get(key))
        
        perihelion_au = find_value('q')
        aphelion_au = find_value('ad')
        
        if not perihelion_au or not aphelion_au:
            semi_major_au = find_value('a')
            eccentricity = find_value('e')
            if semi_major_au and eccentricity:
                if not perihelion_au:
                    perihelion_au = semi_major_au * (1 - eccentricity)
                if not aphelion_au:
                    aphelion_au = semi_major_au * (1 + eccentricity)
        
        return perihelion_au, aphelion_au
    
    def _extract_earth_moid(self, orbit: Dict) -> Optional[float]:
        """Извлекает MOID Земли из орбитальных данных."""
        moid_data = orbit.get('moid')
        if isinstance(moid_data, dict):
            return self._extract_astro_value(moid_data.get('earth'))
        else:
            return self._extract_astro_value(orbit.get('moid_earth')) or self._extract_astro_value(moid_data)
    
    def _extract_absolute_magnitude(self, phys_par: Dict, obj: Dict, designation: str) -> float:
        """Извлекает абсолютную звездную величину (H)."""
        h_sources = [phys_par.get('H'), obj.get('H'), phys_par.get('h'), obj.get('h')]
        
        for source in h_sources:
            h_mag = self._extract_astro_value(source)
            if h_mag is not None:
                return h_mag
        
        logger.debug(f"Астероид {designation} без H-величины. Используем H=18.0")
        return 18.0
    
    def _extract_albedo(self, phys_par: Dict, obj: Dict) -> tuple:
        """Извлекает альбедо и флаг наличия данных."""
        albedo_sources = [
            phys_par.get('albedo'),
            phys_par.get('p_v'),
            phys_par.get('pv'),
            phys_par.get('albedo_value'),
            phys_par.get('albedo_vis'),
            obj.get('albedo'),
            obj.get('p_v'),
        ]
        
        for source in albedo_sources:
            extracted = self._extract_astro_value(source)
            if extracted is not None and 0 < extracted <= 1:
                return extracted, True
        
        return 0.15, False
    
    def _extract_diameter(self, phys_par: Dict, obj: Dict, h_mag: float, 
                         albedo: float, has_albedo_data: bool) -> tuple:
        """Извлекает диаметр, источник данных и флаг точности."""
        diameter_sources = [
            phys_par.get('diameter'),
            phys_par.get('diameter_km'),
            phys_par.get('diam'),
            phys_par.get('size'),
            phys_par.get('est_diameter'),
            phys_par.get('diameter_value'),
            obj.get('diameter'),
            obj.get('diameter_km'),
        ]
        
        for source in diameter_sources:
            extracted = self._extract_astro_value(source)
            if extracted is not None and extracted > 0:
                diameter_is_measured = self._is_diameter_measured(phys_par)
                diameter_source = 'measured' if diameter_is_measured else 'computed'
                accurate_diameter = diameter_is_measured
                return extracted, diameter_source, accurate_diameter
        
        return self._calculate_diameter(h_mag, albedo, has_albedo_data), 'calculated', False
    
    def _is_diameter_measured(self, phys_par: Dict) -> bool:
        """Определяет, является ли диаметр измеренным или вычисленным."""
        diameter_ref = phys_par.get('diameter_ref', '')
        diameter_note = phys_par.get('diameter_note', '')
        ref_note = f"{diameter_ref} {diameter_note}".lower()
        
        measured_keywords = [
            'radar', 'IRAS', 'WISE', 'NEOWISE', 'Spitzer', 
            'thermal', 'occultation', 'adaptive optics',
            'HST', 'Hubble', 'Keck', 'VLT', 'Arecibo'
        ]
        
        computed_keywords = [
            'assumed', 'assumed albedo', 'typical', 'standard',
            'default', 'estimated from', 'derived from'
        ]
        
        if any(keyword in ref_note for keyword in measured_keywords):
            return True
        elif any(keyword in ref_note for keyword in computed_keywords):
            return False
        
        return True
    
    def _calculate_diameter(self, h_mag: float, albedo: float, has_albedo_data: bool) -> float:
        """Вычисляет диаметр на основе H-величины и альбедо."""
        try:
            if has_albedo_data:
                return get_size_by_albedo(albedo, h_mag)
            else:
                return get_size_by_h_mag(h_mag)
        except Exception:
            return get_size_by_h_mag(h_mag)
    
    def _extract_astro_value(self, value):
        """Извлекает числовое значение из различных форматов данных NASA SBDB."""
        if value is None:
            return None
        
        try:
            if hasattr(value, 'value'):
                return float(value.value)
            
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, dict):
                for key in ['value', 'est', 'val', 'mean']:
                    if key in value and value[key] is not None:
                        return self._extract_astro_value(value[key])
            
            if isinstance(value, str):
                clean = value.strip().lower()
                number_pattern = r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?'
                numbers = re.findall(number_pattern, clean)
                
                if numbers:
                    main_value = float(numbers[0])
                    
                    if 'km' in clean and 'm' not in clean.replace('km', ''):
                        return main_value
                    elif 'm' in clean and 'km' not in clean.replace('m', ''):
                        return main_value / 1000
                    elif 'au' in clean:
                        return main_value * 149597870.7
                    else:
                        return main_value
            
            if isinstance(value, (list, tuple)) and len(value) > 0:
                return self._extract_astro_value(value[0])
                
        except (ValueError, TypeError, AttributeError):
            pass
        
        return None
    
    def _create_fallback_asteroid(self, designation: str) -> Dict[str, Any]:
        """Создает минимальные данные об астероиде при ошибке парсинга."""
        return {
            'designation': designation,
            'name': None,
            'perihelion_au': None,
            'aphelion_au': None,
            'earth_moid_au': None,
            'absolute_magnitude': 18.0,
            'estimated_diameter_km': get_size_by_h_mag(18.0),
            'accurate_diameter': False,
            'albedo': 0.15,
            'orbit_class': 'Unknown',
            'orbit_id': None,
        }
    
    def _log_diameter_statistics(self, results: List[Dict[str, Any]]) -> None:
        """Логирует статистику по диаметрам астероидов."""
        accurate_count = sum(1 for a in results if a.get('accurate_diameter', False))
        measured_count = sum(1 for a in results if a.get('diameter_source') == 'measured')
        computed_count = sum(1 for a in results if a.get('diameter_source') == 'computed')
        calculated_count = sum(1 for a in results if a.get('diameter_source') == 'calculated')
        total = len(results)
        
        logger.info(f"Статистика по диаметрам:")
        logger.info(f"  Всего астероидов: {total}")
        logger.info(f"  Точные диаметры: {accurate_count} ({accurate_count/total*100:.1f}%)")
        logger.info(f"  Измеренные диаметры: {measured_count} ({measured_count/total*100:.1f}%)")
        logger.info(f"  Вычисленные NASA: {computed_count} ({computed_count/total*100:.1f}%)")
        logger.info(f"  Рассчитанные программой: {calculated_count} ({calculated_count/total*100:.1f}%)")
    
    async def _get_pha_list(self, limit: Optional[int]) -> List[str]:
        """Асинхронно получает список обозначений PHA."""
        params = {
            'fields': 'pdes',
            'sb-group': 'pha',
            'limit': limit or 3000
        }
        
        try:
            async with self.session.get(self.SBDB_QUERY_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if 'data' not in data:
                    return []
                    
                return [item[0] for item in data.get('data', [])]
                
        except Exception as e:
            logger.error(f"Ошибка получения списка PHA: {e}")
            return []
        