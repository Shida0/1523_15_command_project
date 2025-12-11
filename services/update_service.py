"""
Оптимизированный сервис ежедневного обновления данных.
Использует параллельные запросы и реальные данные из MPC/JPL.
"""
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.ext.asyncio import AsyncSession

from controllers.asteroid_controller import AsteroidController
from controllers.approach_controller import ApproachController
from controllers.threat_controller import ThreatController
from .base_service import BaseService
from .math_service import SpaceMathService

# Импорт утилит
from utils.get_data import get_neo
from utils.monitoring import get_current_close_approaches
from utils.space_math import count_danger

logger = logging.getLogger(__name__)


class DataUpdateService(BaseService):
    """Оптимизированный сервис для ежедневного обновления данных."""
    
    def __init__(self, max_workers: int = 5):
        """Инициализирует сервис с параллельной обработкой."""
        super().__init__()
        self.asteroid_controller = AsteroidController()
        self.approach_controller = ApproachController()
        self.threat_controller = ThreatController()
        self.math_service = SpaceMathService()
        self.max_workers = max_workers
        logger.info(f"Инициализирован DataUpdateService (max_workers={max_workers})")
    
    async def run_daily_update(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Выполняет полный цикл ежедневного обновления данных с оптимизациями.
        
        Args:
            session: Сессия БД
            
        Returns:
            Словарь с результатами обновления
        """
        self.log_service_call("run_daily_update")
        
        try:
            start_time = datetime.now()
            update_id = f"update_{start_time.strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🚀 Начало оптимизированного обновления {update_id}")
            
            # 1. Получение данных из MPC (синхронно, т.к. astroquery синхронный)
            logger.info("📥 Этап 1: Получение данных из MPC...")
            neo_data = await self._async_get_neo()
            
            if not neo_data:
                raise ValueError("Не удалось получить данные из MPC")
            
            # 2. Фильтрация PHA (MOID < 0.05 а.е.)
            logger.info("🎯 Этап 2: Фильтрация потенциально опасных астероидов...")
            pha_data = self._filter_pha_asteroids(neo_data)
            
            if not pha_data:
                logger.warning("Не найдено потенциально опасных астероидов")
                return self._create_empty_result(update_id, start_time)
            
            # 3. Обновление данных астероидов в БД
            logger.info("💾 Этап 3: Обновление данных астероидов в БД...")
            created_asteroids, updated_asteroids = await self._bulk_upsert_asteroids(
                session, pha_data
            )
            
            # 4. Параллельный расчет сближений для каждого PHA
            logger.info("🔄 Этап 4: Параллельный расчет сближений на 10 лет...")
            all_approaches = await self._parallel_calculate_approaches(pha_data)
            
            # 5. Массовое сохранение сближений в БД
            logger.info("💿 Этап 5: Массовое сохранение сближений в БД...")
            saved_approaches = await self._bulk_save_approaches(
                session, all_approaches, update_id
            )
            
            # 6. Расчет оценок угроз для сближений
            logger.info("⚠️ Этап 6: Расчет оценок угроз...")
            saved_threats = await self._calculate_and_save_threats(
                session, all_approaches, update_id
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
                "performance": {
                    "asteroids_per_second": round(len(pha_data) / duration, 2) if duration > 0 else 0,
                    "approaches_per_second": round(len(all_approaches) / duration, 2) if duration > 0 else 0
                },
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
                }
            }
            
            logger.info(
                f"✅ Обновление {update_id} завершено за {duration:.2f} секунд. "
                f"Обработано: {len(pha_data)} PHA, {len(all_approaches)} сближений"
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
        
        # Запускаем в отдельном потоке, чтобы не блокировать event loop
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
            
            # Критерий PHA: MOID < 0.05 а.е. ИЛИ флаг is_pha = True
            if moid < 0.05 or is_pha:
                # Преобразуем в формат модели
                formatted = self._format_asteroid_data(asteroid)
                pha_data.append(formatted)
        
        logger.info(f"Отфильтровано {len(pha_data)} PHA из {len(neo_data)} NEO")
        return pha_data
    
    def _format_asteroid_data(self, asteroid_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует данные из MPC в формат AsteroidModel.
        
        Args:
            asteroid_data: Данные из MPC
            
        Returns:
            Форматированные данные
        """
        return {
            "mpc_number": asteroid_data.get('mpc_number'),
            "name": asteroid_data.get('name'),
            "designation": asteroid_data.get('designation'),
            "perihelion_au": asteroid_data.get('perihelion_au', 0.5),
            "aphelion_au": asteroid_data.get('aphelion_au', 1.5),
            "earth_moid_au": asteroid_data.get('earth_moid_au', 0.1),
            "absolute_magnitude": asteroid_data.get('absolute_magnitude', 20.0),
            "estimated_diameter_km": asteroid_data.get('estimated_diameter_km', 0.1),
            "accurate_diameter": asteroid_data.get('accurate_diameter', False),
            "albedo": asteroid_data.get('albedo', 0.15),
            "is_neo": asteroid_data.get('is_neo', True),
            "is_pha": asteroid_data.get('is_pha', False)
        }
    
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
    
    async def _parallel_calculate_approaches(
        self, 
        asteroids_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Параллельный расчет сближений для всех астероидов.
        
        Args:
            asteroids_data: Данные астероидов
            
        Returns:
            Список всех сближений
        """
        loop = asyncio.get_event_loop()
        all_approaches = []
        
        # Группируем астероиды для параллельной обработки
        asteroid_chunks = self._chunk_list(asteroids_data, self.max_workers)
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for chunk in asteroid_chunks:
            task = loop.run_in_executor(
                None,  # Используем дефолтный executor
                self._sync_calculate_chunk_approaches,
                chunk
            )
            tasks.append(task)
        
        # Ждем завершения всех задач
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем результаты
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ошибка при расчете сближений: {result}")
            elif result:
                all_approaches.extend(result)
        
        logger.info(f"Рассчитано {len(all_approaches)} сближений в {len(asteroid_chunks)} потоках")
        return all_approaches
    
    def _sync_calculate_chunk_approaches(
        self, 
        asteroids_chunk: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Синхронный расчет сближений для чанка астероидов.
        
        Args:
            asteroids_chunk: Чанк астероидов
            
        Returns:
            Сближения для чанка
        """
        approaches = []
        
        for asteroid in asteroids_chunk:
            try:
                asteroid_approaches = self._calculate_approaches_for_asteroid(asteroid)
                approaches.extend(asteroid_approaches)
            except Exception as e:
                logger.error(f"Ошибка расчета для астероида {asteroid.get('mpc_number')}: {e}")
                continue
        
        return approaches
    
    def _calculate_approaches_for_asteroid(
        self, 
        asteroid_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитывает сближения для одного астероида на 10 лет вперед.
        ИСПОЛЬЗУЕТСЯ РЕАЛЬНАЯ ЛОГИКА ИЗ monitoring.py
        
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
            # Используем реальную функцию из monitoring.py
            # Для расчета на 10 лет (3650 дней) используем оптимизированный подход
            approaches_data = get_current_close_approaches([asteroid_data], days=3650)
            
            # Преобразуем формат
            formatted_approaches = []
            for approach in approaches_data:
                # Фильтруем только сближения ближе 1 а.е.
                if approach['distance_au'] < 1.0:
                    formatted = {
                        "asteroid_id": None,  # Заполнится позже
                        "mpc_number": mpc_number,
                        "approach_time": datetime.strptime(
                            approach['approach_date'], 
                            '%Y-%b-%d %H:%M'
                        ) if isinstance(approach['approach_date'], str) else approach['approach_date'],
                        "distance_au": approach['distance_au'],
                        "distance_km": approach['distance_km'],
                        "velocity_km_s": approach['velocity_km_s'],
                        "is_close": approach['distance_au'] < 0.1
                    }
                    formatted_approaches.append(formatted)
            
            return formatted_approaches
            
        except Exception as e:
            logger.error(f"Ошибка расчета сближений для MPC {mpc_number}: {e}")
            return []
    
    async def _bulk_save_approaches(
        self, 
        session: AsyncSession, 
        approaches: List[Dict[str, Any]],
        batch_id: str
    ) -> int:
        """
        Массовое сохранение сближений с оптимизацией.
        
        Args:
            session: Сессия БД
            approaches: Список сближений
            batch_id: ID партии
            
        Returns:
            Количество сохраненных
        """
        if not approaches:
            return 0
        
        # Группируем по MPC для эффективной обработки
        mpc_groups = {}
        for approach in approaches:
            mpc = approach.get('mpc_number')
            if mpc not in mpc_groups:
                mpc_groups[mpc] = []
            mpc_groups[mpc].append(approach)
        
        total_saved = 0
        
        # Обрабатываем каждую группу
        for mpc, group_approaches in mpc_groups.items():
            # Находим asteroid_id для этой группы
            asteroid = await self.asteroid_controller.get_by_mpc_number(session, mpc)
            
            if not asteroid:
                logger.warning(f"Астероид MPC {mpc} не найден в БД, пропускаем {len(group_approaches)} сближений")
                continue
            
            # Обновляем данные для массовой вставки
            for approach in group_approaches:
                approach['asteroid_id'] = asteroid.id
                approach['calculation_batch_id'] = batch_id
                # Удаляем временные поля
                approach.pop('mpc_number', None)
                approach.pop('is_close', None)
            
            # Массовое сохранение
            saved = await self.approach_controller.bulk_create_approaches(
                session, group_approaches, batch_id
            )
            total_saved += saved
        
        logger.info(f"Сохранено {total_saved} сближений из {len(approaches)} рассчитанных")
        return total_saved
    
    async def _calculate_and_save_threats(
        self, 
        session: AsyncSession, 
        approaches: List[Dict[str, Any]],
        batch_id: str
    ) -> int:
        """
        Рассчитывает и сохраняет оценки угроз для сближений.
        
        Args:
            session: Сессия БД
            approaches: Список сближений
            batch_id: ID партии
            
        Returns:
            Количество сохраненных оценок
        """
        threats_data = []
        
        for approach in approaches:
            if not approach.get('asteroid_id'):
                continue
            
            # Получаем данные астероида
            asteroid = await self.asteroid_controller.get_by_id(
                session, approach['asteroid_id']
            )
            
            if not asteroid:
                continue
            
            # Рассчитываем оценку угрозы
            threat_assessment = count_danger(
                diameter_km=asteroid.estimated_diameter_km,
                distance_au=approach['distance_au'],
                velocity_km_s=approach['velocity_km_s']
            )
            
            # Преобразуем результат в формат ThreatAssessmentModel
            threat_data = {
                "approach_id": None,  # Заполнится позже
                "threat_level": self._translate_threat_level(threat_assessment.get('итоговая оценка', {}).get('степень угрозы', 'низкий')),
                "impact_category": self._translate_impact_category(threat_assessment.get('анализ параметров', {}).get('категория воздействия', 'локальный')),
                "energy_megatons": threat_assessment.get('энергетическая оценка', {}).get('эквивалент мегатонн', 0.0),
                "calculation_input_hash": self._calculate_threat_hash(
                    asteroid.estimated_diameter_km,
                    approach['distance_au'],
                    approach['velocity_km_s']
                )
            }
            
            threats_data.append({
                'approach_data': approach,
                'threat_data': threat_data
            })
        
        # Сохраняем оценки угроз
        saved_threats = 0
        for item in threats_data:
            # Находим ID сближения по времени и астероиду
            approach = await self._find_approach_by_data(
                session,
                item['approach_data']['asteroid_id'],
                item['approach_data']['approach_time']
            )
            
            if approach:
                item['threat_data']['approach_id'] = approach.id
                await self.threat_controller.create(session, item['threat_data'])
                saved_threats += 1
        
        logger.info(f"Сохранено {saved_threats} оценок угроз")
        return saved_threats
    
    async def _find_approach_by_data(
        self, 
        session: AsyncSession, 
        asteroid_id: int, 
        approach_time: datetime
    ) -> Optional[Any]:
        """Находит сближение по данным."""
        from models.close_approach import CloseApproachModel
        from sqlalchemy import select
        
        query = select(CloseApproachModel).where(
            (CloseApproachModel.asteroid_id == asteroid_id) &
            (CloseApproachModel.approach_time == approach_time)
        )
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _cleanup_old_data(self, session: AsyncSession) -> Dict[str, int]:
        """
        Очищает устаревшие данные.
        
        Args:
            session: Сессия БД
            
        Returns:
            Статистика очистки
        """
        stats = {}
        
        # Удаляем прошедшие сближения (старше вчерашнего дня)
        yesterday = datetime.now() - timedelta(days=1)
        deleted_past = await self.approach_controller.delete_old_approaches(
            session, yesterday
        )
        stats['deleted_past_approaches'] = deleted_past
        
        # Удаляем сближения за пределами 10-летнего окна
        future_limit = datetime.now() + timedelta(days=3650)
        deleted_future = await self._delete_outdated_future_approaches(
            session, future_limit
        )
        stats['deleted_future_approaches'] = deleted_future
        
        logger.info(f"Очистка: удалено {deleted_past} прошедших и {deleted_future} будущих сближений")
        return stats
    
    async def _delete_outdated_future_approaches(
        self, 
        session: AsyncSession, 
        cutoff_date: datetime
    ) -> int:
        """Удаляет сближения за пределами временного окна."""
        from models.close_approach import CloseApproachModel
        from sqlalchemy import select, delete
        
        try:
            # Находим ID для удаления
            query = select(CloseApproachModel.id).where(
                CloseApproachModel.approach_time > cutoff_date
            )
            result = await session.execute(query)
            ids_to_delete = [row[0] for row in result]
            
            if not ids_to_delete:
                return 0
            
            # Удаляем оценки угроз
            from models.threat_assessment import ThreatAssessmentModel
            delete_threats = delete(ThreatAssessmentModel).where(
                ThreatAssessmentModel.approach_id.in_(ids_to_delete)
            )
            await session.execute(delete_threats)
            
            # Удаляем сближения
            delete_approaches = delete(CloseApproachModel).where(
                CloseApproachModel.id.in_(ids_to_delete)
            )
            result = await session.execute(delete_approaches)
            
            await session.commit()
            return result.rowcount
            
        except Exception as e:
            logger.error(f"Ошибка удаления будущих сближений: {e}")
            await session.rollback()
            return 0
    
    def _translate_threat_level(self, ru_level: str) -> str:
        """Переводит уровень угрозы с русского на английский."""
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
    
    def _calculate_threat_hash(
        self, 
        diameter_km: float, 
        distance_au: float, 
        velocity_km_s: float
    ) -> str:
        """Вычисляет хеш входных данных для оценки угрозы."""
        import hashlib
        input_str = f"{diameter_km:.4f}:{distance_au:.6f}:{velocity_km_s:.2f}"
        return hashlib.sha256(input_str.encode()).hexdigest()
    
    def _chunk_list(self, lst: List, n: int):
        """Разбивает список на чанки."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def _create_empty_result(self, update_id: str, start_time: datetime) -> Dict[str, Any]:
        """Создает результат для пустого обновления."""
        return {
            "update_id": update_id,
            "status": "success",
            "duration_seconds": 0,
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