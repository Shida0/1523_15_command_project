"""
Оптимизированный сервис ежедневного обновления данных.
Реальная работа с MPC, JPL Horizons и асинхронной БД.
"""
import threading
from typing import Dict, List, Any, Optional, Tuple 
from datetime import datetime, timedelta
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import time

from sqlalchemy import exists
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.asteroid_controller import AsteroidController
from controllers.approach_controller import ApproachController
from controllers.threat_controller import ThreatController
from models.threat_assessment import ThreatAssessmentModel
from .base_service import BaseService

# Импорт реальных утилит
from utils.get_data import get_neo
from utils.space_math import count_danger

logger = logging.getLogger(__name__)


class DataUpdateService(BaseService):
    """Реальный сервис для ежедневного обновления данных."""
    
    def __init__(self, max_workers: int = 3):  # Уменьшил для JPL Horizons
        """Инициализирует сервис с учетом ограничений JPL API."""
        super().__init__()
        self.asteroid_controller = AsteroidController()
        self.approach_controller = ApproachController()
        self.threat_controller = ThreatController()
        self.max_workers = max_workers
        logger.info(f"Инициализирован DataUpdateService (max_workers={max_workers})")
    
    async def run_daily_update(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Выполняет полный цикл ежедневного обновления данных.
        
        Args:
            session: Сессия БД
            
        Returns:
            Словарь с результатами обновления
        """
        self.log_service_call("run_daily_update")
        
        try:
            start_time = datetime.now()
            update_id = f"update_{start_time.strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🚀 Начало обновления {update_id}")
            
            # 1. Получение данных из MPC
            logger.info("📥 Этап 1: Получение данных из MPC...")
            neo_data = await self._async_get_neo()
            
            if not neo_data:
                logger.warning("Не получены данные из MPC")
                return self._create_empty_result(update_id, start_time)
            
            logger.info(f"Получено {len(neo_data)} NEO из MPC")
            
            # 2. Фильтрация PHA (MOID < 0.05 а.е.)
            logger.info("🎯 Этап 2: Фильтрация потенциально опасных астероидов...")
            pha_data = self._filter_pha_asteroids(neo_data)
            
            if not pha_data:
                logger.warning("Не найдено потенциально опасных астероидов")
                return self._create_empty_result(update_id, start_time)
            
            logger.info(f"Отфильтровано {len(pha_data)} PHA астероидов")
            
            # 3. Обновление данных астероидов в БД
            logger.info("💾 Этап 3: Обновление данных астероидов в БД...")
            created_asteroids, updated_asteroids = await self._bulk_upsert_asteroids(
                session, pha_data
            )
            
            logger.info(f"Создано: {created_asteroids}, Обновлено: {updated_asteroids}")
            
            # 4. Расчет сближений для PHA (МАКСИМАЛЬНО оптимизировано)
            logger.info("🔄 Этап 4: Расчет сближений на 10 лет...")
            all_approaches = await self._optimized_calculate_approaches(session, pha_data)
            
            # 5. Сохранение сближений в БД
            logger.info("💿 Этап 5: Сохранение сближений в БД...")
            saved_approaches = await self._bulk_save_approaches(
                session, all_approaches, update_id
            )
            
            # 6. Расчет оценок угроз (опционально, можно делать позже)
            logger.info("⚠️ Этап 6: Расчет оценок угроз...")
            saved_threats = await self._calculate_and_save_threats(
                session, all_approaches
            )
            
            # 7. Очистка устаревших данных
            logger.info("🗑️ Этап 7: Очистка устаревших данных...")
            cleanup_stats = await self._cleanup_old_data(session)
            
            # Формирование отчета
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            report = {
                "update_id": update_id,
                "status": "success",
                "duration_seconds": round(duration, 2),
                "duration_human": str(timedelta(seconds=int(duration))),
                "asteroids": {
                    "total_neo": len(neo_data),
                    "pha_count": len(pha_data),
                    "created": created_asteroids,
                    "updated": updated_asteroids
                },
                "approaches": {
                    "calculated": len(all_approaches),
                    "saved": saved_approaches,
                    "with_threats": saved_threats
                },
                "cleanup": cleanup_stats,
                "timestamps": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "performance": {
                    "asteroids_per_second": (created_asteroids + updated_asteroids)/round(duration, 2)
                },
                "notes": [
                    "Для JPL Horizons запросы выполнялись с задержкой 2 секунды",
                    f"Использовано потоков: {self.max_workers}"
                ]
            }
            
            logger.info(
                f"✅ Обновление {update_id} завершено за {duration:.2f} секунд. "
                f"Обработано: {len(pha_data)} PHA, {saved_approaches} сближений"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения обновления: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    async def _async_get_neo(self) -> List[Dict[str, Any]]:
        """
        Асинхронный запуск синхронной функции get_neo.
        
        Returns:
            Данные NEO из MPC
        """
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            neo_data = await loop.run_in_executor(executor, get_neo)
        
        return neo_data
    
    def _filter_pha_asteroids(self, neo_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует потенциально опасные астероиды.
        
        Args:
            neo_data: Список NEO
            
        Returns:
            Отфильтрованные PHA
        """
        pha_data = []
        
        for asteroid in neo_data:
            moid = asteroid.get('earth_moid_au', 1.0)
            is_pha = asteroid.get('is_pha', False)
            
            # Критерий PHA: MOID < 0.05 а.е.
            if moid < 0.05:
                pha_data.append(asteroid)
        
        logger.info(f"Отфильтровано {len(pha_data)} PHA из {len(neo_data)} NEO")
        return pha_data
    
    async def _bulk_upsert_asteroids(
        self, 
        session: AsyncSession, 
        asteroids_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Массовое обновление/вставка астероидов.
        
        Args:
            session: Сессия БД
            asteroids_data: Данные астероидов
            
        Returns:
            (создано, обновлено)
        """
        return await self.asteroid_controller.bulk_create(session, asteroids_data)
    
    async def _optimized_calculate_approaches(
        self, 
        session: AsyncSession,
        asteroids_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Оптимизированный расчет сближений с учетом лимитов JPL API.
        
        Args:
            session: Сессия БД
            asteroids_data: Данные астероидов
            
        Returns:
            Список всех сближений
        """
        all_approaches = []
        
        # Ограничиваем количество астероидов для расчета (для теста)
        max_asteroids = min(50, len(asteroids_data))
        asteroids_to_process = asteroids_data[:max_asteroids]
        
        logger.info(f"Расчет сближений для {max_asteroids} астероидов (из {len(asteroids_data)})")
        
        # Обрабатываем в потоках с ограничением
        loop = asyncio.get_event_loop()
        
        # Разбиваем на чанки по max_workers
        chunk_size = max(1, len(asteroids_to_process) // self.max_workers)
        chunks = [
            asteroids_to_process[i:i + chunk_size] 
            for i in range(0, len(asteroids_to_process), chunk_size)
        ]
        
        tasks = []
        for chunk in chunks:
            task = loop.run_in_executor(
                None,
                self._sync_calculate_chunk_approaches,
                chunk
            )
            tasks.append(task)
        
        # Собираем результаты
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ошибка при расчете сближений: {result}")
            elif result:
                all_approaches.extend(result)
        
        logger.info(f"Рассчитано {len(all_approaches)} сближений")
        return all_approaches
    
    def _sync_calculate_chunk_approaches(self, asteroids_chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Синхронный расчет сближений для чанка астероидов."""
        approaches = []
        thread_logger = logging.getLogger(f"{__name__}.thread.{threading.get_ident()}")
        
        for i, asteroid in enumerate(asteroids_chunk):
            try:
                # Задержка для JPL API (не блокирующая для event loop)
                if i > 0:
                    time.sleep(2)
                
                asteroid_approaches = self._calculate_approaches_for_asteroid(asteroid)
                approaches.extend(asteroid_approaches)
                
                thread_logger.debug(f"Обработан астероид {asteroid.get('mpc_number')}: {len(asteroid_approaches)} сближений")
                
            except Exception as e:
                thread_logger.error(f"Ошибка расчета для астероида {asteroid.get('mpc_number')}: {e}")
                continue
        
        return approaches
    
    def _calculate_approaches_for_asteroid(
        self, 
        asteroid_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитывает сближения для одного астероида на 10 лет вперед.
        
        Args:
            asteroid_data: Данные астероида
            
        Returns:
            Список сближений
        """
        from utils.monitoring import get_current_close_approaches
        
        mpc_number = asteroid_data.get('mpc_number')
        if not mpc_number:
            return []
        
        try:
            # Преобразуем в формат, который ожидает monitoring.py
            asteroid_for_monitoring = {
                'number': str(mpc_number),
                'name': asteroid_data.get('name', ''),
                'is_pha': asteroid_data.get('is_pha', False),
                'mpc_number': mpc_number,
                'designation': asteroid_data.get('designation', '')  # ❗ JPL часто требует designation!
            }
            
            # Рассчитываем сближения на 10 лет
            approaches_data = get_current_close_approaches([asteroid_for_monitoring], days=3650)
            
            # Преобразуем в наш формат
            formatted_approaches = []
            for approach in approaches_data:
                # Только сближения ближе 1 а.е.
                if approach.get('distance_au', 10.0) < 1.0:
                    parsed_date = self._parse_approach_date(approach.get('approach_date'))
                    formatted = {
                        "asteroid_id": None,
                        "mpc_number": mpc_number,
                        "approach_time": parsed_date,
                        "distance_au": approach.get('distance_au', 1.0),
                        "distance_km": approach.get('distance_km', 149597870.7),
                        "velocity_km_s": approach.get('velocity_km_s', 20.0),
                        "is_close": approach.get('distance_au', 1.0) < 0.1
                    }
                    
                    # ❗ ПРОВЕРЯЕМ перед добавлением:
                    if parsed_date is not None:
                        formatted_approaches.append(formatted)
                    else:
                        logger.warning(f"Пропущено сближение с некорректной датой для MPC {mpc_number}")
                    formatted_approaches.append(formatted)
            
            return formatted_approaches
            
        except Exception as e:
            logger.error(f"Ошибка расчета сближений для MPC {mpc_number}: {e}")
            return []
    
    def _parse_approach_date(self, date_str: Any) -> Optional[datetime]:
        """
        Парсит дату сближения из различных форматов.
        Возвращает None при ошибке вместо случайной даты!
        """
        if isinstance(date_str, datetime):
            return date_str
        
        if not isinstance(date_str, str):
            logger.warning(f"Некорректный тип даты: {type(date_str)}")
            return None
        
        # Список возможных форматов JPL Horizons
        formats = [
            '%Y-%b-%d %H:%M',      # 2024-Dec-12 12:34
            '%Y-%m-%d %H:%M',      # 2024-12-12 12:34
            '%Y-%b-%d %H:%M:%S',   # 2024-Dec-12 12:34:56
            '%Y-%m-%d %H:%M:%S',   # 2024-12-12 12:34:56
            '%Y-%b-%d',            # 2024-Dec-12
            '%Y-%m-%d',            # 2024-12-12
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.error(f"Не удалось распарсить дату: {date_str}")
        return None  # ❗ ВОЗВРАЩАЕМ None, а не случайную дату!

    
    
    async def _bulk_save_approaches(self, session: AsyncSession, approaches: List[Dict[str, Any]], batch_id: str) -> int:
        """Массовое сохранение сближений с БАТЧ-запросами."""
        if not approaches:
            return 0
        
        from models.asteroid import AsteroidModel
        from sqlalchemy import select
        
        # 1. ОДИН ЗАПРОС для всех астероидов
        all_mpc_numbers = list({approach.get('mpc_number') for approach in approaches 
                            if approach.get('mpc_number') is not None})
        
        if not all_mpc_numbers:
            return 0
        
        # БАТЧ запрос к БД
        query = select(AsteroidModel).where(AsteroidModel.mpc_number.in_(all_mpc_numbers))
        result = await session.execute(query)
        asteroids = result.scalars().all()
        
        # Создаем маппинг
        mpc_to_id = {asteroid.mpc_number: asteroid.id for asteroid in asteroids}
        
        # 2. ПОДГОТОВКА ДАННЫХ ДЛЯ МАССОВОЙ ВСТАВКИ
        valid_approaches = []
        missing_asteroids = set()
        
        for approach in approaches:
            mpc = approach.get('mpc_number')
            asteroid_id = mpc_to_id.get(mpc)
            
            if asteroid_id:
                # БЕЗОПАСНОЕ удаление ключей
                approach_copy = approach.copy()
                approach_copy['asteroid_id'] = asteroid_id
                approach_copy['calculation_batch_id'] = batch_id
                approach_copy.pop('mpc_number', None)  # ❗ pop с default
                approach_copy.pop('is_close', None)
                valid_approaches.append(approach_copy)
            else:
                missing_asteroids.add(mpc)
        
        if missing_asteroids:
            logger.warning(f"Астероиды не найдены в БД: {missing_asteroids}")
        
        # 3. МАССОВАЯ ВСТАВКА
        if valid_approaches:
            saved = await self.approach_controller.bulk_create_approaches(
                session, valid_approaches, batch_id
            )
            logger.info(f"Сохранено {saved} сближений")
            return saved
        
        return 0
    
    async def _calculate_and_save_threats(self, session: AsyncSession, approaches: List[Dict[str, Any]]) -> int:
        """Оптимизированный расчет и сохранение оценок угроз."""
        from models.close_approach import CloseApproachModel
        from models.asteroid import AsteroidModel
        from sqlalchemy import select, join
        
        # 1. ОДИН ЗАПРОС: все подходы с данными астероидов
        query = select(
            CloseApproachModel.id,
            CloseApproachModel.distance_au,
            CloseApproachModel.velocity_km_s,
            AsteroidModel.estimated_diameter_km
        ).join(
            AsteroidModel, 
            CloseApproachModel.asteroid_id == AsteroidModel.id
        ).where(
            ~exists().where(ThreatAssessmentModel.approach_id == CloseApproachModel.id)  # Только без оценок
        )
        
        result = await session.execute(query)
        data = result.all()
        
        if not data:
            return 0
        
        # 2. МАССОВЫЙ РАСЧЕТ
        threats_to_save = []
        for approach_id, distance_au, velocity_km_s, diameter_km in data:
            try:
                threat_result = count_danger(
                    diameter_km=diameter_km,
                    distance_au=distance_au,
                    velocity_km_s=velocity_km_s
                )
                
                threat_data = {
                    "approach_id": approach_id,
                    "threat_level": self._get_threat_level(
                        threat_result.get('итоговая оценка', {}).get('степень угрозы', 'низкий')
                    ),
                    "impact_category": self._get_impact_category(
                        threat_result.get('анализ параметров', {}).get('категория воздействия', 'локальный')
                    ),
                    "energy_megatons": threat_result.get('энергетическая оценка', {}).get('эквивалент мегатонн', 0.0)
                }
                
                threats_to_save.append(threat_data)
                
                # Пачка по 100 записей
                if len(threats_to_save) >= 100:
                    await self.threat_controller.bulk_create_assessments(session, threats_to_save)
                    threats_to_save = []
                    
            except Exception as e:
                logger.error(f"Ошибка расчета угрозы для подхода {approach_id}: {e}")
                continue
        
        # Остатки
        if threats_to_save:
            await self.threat_controller.bulk_create_assessments(session, threats_to_save)
        
        return len(data)
    
    async def _cleanup_old_data(self, session: AsyncSession) -> Dict[str, int]:
        """
        Очищает устаревшие данные В РАЗНЫХ ТРАНЗАКЦИЯХ!
        """
        stats = {}
        
        # 1. Удаляем прошедшие сближения в ОТДЕЛЬНОЙ транзакции
        try:
            yesterday = datetime.now() - timedelta(days=1)
            deleted_past = await self.approach_controller.delete_old_approaches(
                session, yesterday
            )
            stats['deleted_past_approaches'] = deleted_past
            
            await session.commit()  # ❗ КОММИТИМ первую транзакцию
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка удаления прошедших сближений: {e}")
        
        # 2. Удаляем будущие сближения в НОВОЙ транзакции
        try:
            future_limit = datetime.now() + timedelta(days=3650)
            deleted_future = await self._delete_outdated_future_approaches(
                session, future_limit
            )
            stats['deleted_future_approaches'] = deleted_future
            
            await session.commit()  # ❗ КОММИТИМ вторую транзакцию
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка удаления будущих сближений: {e}")
        
        return stats
    
    async def _delete_outdated_future_approaches(
        self, 
        session: AsyncSession, 
        cutoff_date: datetime
    ) -> int:
        """Удаляет сближения за пределами временного окна."""
        from models.close_approach import CloseApproachModel
        from sqlalchemy import delete
        
        try:
            delete_stmt = delete(CloseApproachModel).where(
                CloseApproachModel.approach_time > cutoff_date
            )
            result = await session.execute(delete_stmt)
            await session.commit()
            
            return result.rowcount
            
        except Exception as e:
            logger.error(f"Ошибка удаления будущих сближений: {e}")
            await session.rollback()
            return 0
    
    def _translate_threat_level(self, ru_level: str) -> str:
        """Переводит уровень угрозы."""
        translations = {
            'низкий': 'low',
            'средний': 'medium', 
            'высокий': 'high',
            'критический': 'critical'
        }
        return translations.get(ru_level.lower(), 'low')
    
    def _translate_impact_category(self, ru_category: str) -> str:
        """Переводит категорию воздействия."""
        translations = {
            'локальный': 'local',
            'региональный': 'regional',
            'глобальный': 'global',
            'незначительный': 'insignificant'
        }
        return translations.get(ru_category.lower(), 'local')
    
    def _create_empty_result(self, update_id: str, start_time: datetime) -> Dict[str, Any]:
        """Создает результат для пустого обновления."""
        return {
            "update_id": update_id,
            "status": "success",
            "duration_seconds": 0,
            "duration_human": "0:00:00",
            "asteroids": {"total_neo": 0, "pha_count": 0, "created": 0, "updated": 0},
            "approaches": {"calculated": 0, "saved": 0, "with_threats": 0},
            "cleanup": {"deleted_past_approaches": 0, "deleted_future_approaches": 0},
            "timestamps": {
                "start": start_time.isoformat(),
                "end": datetime.now().isoformat()
            }
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Создает ответ об ошибке."""
        return {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }