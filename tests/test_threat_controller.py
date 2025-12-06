import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from controllers.threat_controller import ThreatController
from models.threat_assessment import ThreatAssessmentModel


# Silence logger output during tests
logging.getLogger('controllers.threat_controller').setLevel(logging.CRITICAL)


class FakeScalarResult:
    """Minimal fake for SQLAlchemy Result when using scalar() and scalar_one_or_none()."""
    def __init__(self, value=None):
        self._value = value

    def scalar(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class FakeScalarsResult:
    """Minimal fake for SQLAlchemy Result when using scalars().all()."""
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class FakeResult:
    """Generic fake to support scalars().all() as well as scalar() helpers."""
    def __init__(self, scalar_value=None, scalars_list=None):
        self._scalar_value = scalar_value
        self._scalars_list = scalars_list

    def scalar(self):
        return self._scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalars(self):
        return FakeScalarsResult(self._scalars_list or [])


class TestThreatController(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.controller = ThreatController()
        self.session = AsyncMock()
        # Provide commit and rollback to be awaited
        self.session.commit = AsyncMock()
        self.session.rollback = AsyncMock()

    async def test_get_by_approach_id_found(self):
        threat = MagicMock(spec=ThreatAssessmentModel)
        self.session.execute = AsyncMock(return_value=FakeScalarResult(threat))

        result = await self.controller.get_by_approach_id(self.session, approach_id=42)

        self.assertIs(result, threat)
        self.session.execute.assert_awaited()

    async def test_get_by_approach_id_not_found(self):
        self.session.execute = AsyncMock(return_value=FakeScalarResult(None))

        result = await self.controller.get_by_approach_id(self.session, approach_id=999)

        self.assertIsNone(result)
        self.session.execute.assert_awaited()

    async def test_get_high_threats_returns_sorted_list_with_limit(self):
        items = [MagicMock(spec=ThreatAssessmentModel) for _ in range(3)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        result = await self.controller.get_high_threats(self.session, limit=3)

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()

    async def test_update_assessment_returns_none_when_missing(self):
        # No existing assessment found
        with patch.object(self.controller, 'get_by_approach_id', new=AsyncMock(return_value=None)) as mocked_get, \
             patch.object(self.controller, 'update', new=AsyncMock()) as mocked_update:

            updated = await self.controller.update_assessment(self.session, approach_id=123, new_data={'threat_level': 'высокий'})

            self.assertIsNone(updated)
            mocked_get.assert_awaited_once()
            mocked_update.assert_not_awaited()

    async def test_update_assessment_success_sets_input_hash_to_none(self):
        existing = MagicMock(spec=ThreatAssessmentModel)
        existing.id = 10
        updated_instance = MagicMock(spec=ThreatAssessmentModel)
        updated_instance.id = 10
        updated_instance.calculation_input_hash = 'abc'

        with patch.object(self.controller, 'get_by_approach_id', new=AsyncMock(return_value=existing)) as mocked_get, \
             patch.object(self.controller, 'update', new=AsyncMock(return_value=updated_instance)) as mocked_update:

            result = await self.controller.update_assessment(self.session, approach_id=10, new_data={'energy_megatons': 5.5})

            self.assertIs(result, updated_instance)
            self.assertIsNone(result.calculation_input_hash)
            mocked_get.assert_awaited_once()
            mocked_update.assert_awaited_once()

    async def test_update_assessment_rollback_on_exception(self):
        existing = MagicMock(spec=ThreatAssessmentModel)
        existing.id = 1
        with patch.object(self.controller, 'get_by_approach_id', new=AsyncMock(return_value=existing)), \
             patch.object(self.controller, 'update', new=AsyncMock(side_effect=RuntimeError('boom'))):

            with self.assertRaises(RuntimeError):
                await self.controller.update_assessment(self.session, 1, {'threat_level': 'средний'})

            self.session.rollback.assert_awaited_once()

    async def test_bulk_create_assessments_skip_missing_and_commit_and_count(self):
        data = [
            {'approach_id': None, 'threat_level': 'низкий'},  # skipped
            {'approach_id': 1, 'threat_level': 'высокий'},    # existing -> update
            {'approach_id': 2, 'threat_level': 'средний'},    # new -> create
        ]

        existing = MagicMock(spec=ThreatAssessmentModel)
        with patch.object(self.controller, 'get_by_approach_id', new=AsyncMock(side_effect=[existing, None])) as mocked_get, \
             patch.object(self.controller, 'update_assessment', new=AsyncMock()) as mocked_update_assessment, \
             patch.object(self.controller, 'create', new=AsyncMock()) as mocked_create:

            count = await self.controller.bulk_create_assessments(self.session, data)

            # processed two valid entries
            self.assertEqual(count, 2)
            self.assertEqual(mocked_get.await_count, 2)
            mocked_update_assessment.assert_awaited_once()
            mocked_create.assert_awaited_once()
            self.session.commit.assert_awaited_once()

    async def test_bulk_create_assessments_rollback_on_exception(self):
        data = [{'approach_id': 1, 'threat_level': 'высокий'}]
        with patch.object(self.controller, 'get_by_approach_id', new=AsyncMock(return_value=None)), \
             patch.object(self.controller, 'create', new=AsyncMock(side_effect=RuntimeError('fail'))):

            with self.assertRaises(RuntimeError):
                await self.controller.bulk_create_assessments(self.session, data)

            self.session.rollback.assert_awaited_once()
            self.session.commit.assert_not_awaited()

    async def test_get_statistics_computation(self):
        # Order of calls: total, level low, level medium, level high, level critical, avg energy, max energy
        side_effects = [
            FakeScalarResult(50),    # total
            FakeScalarResult(30),    # низкий
            FakeScalarResult(10),    # средний
            FakeScalarResult(7),     # высокий
            FakeScalarResult(3),     # критический
            FakeScalarResult(2.3456),# avg energy
            FakeScalarResult(9.87),  # max energy
        ]
        self.session.execute = AsyncMock(side_effect=side_effects)

        stats = await self.controller.get_statistics(self.session)

        self.assertEqual(stats['total_assessments'], 50)
        self.assertEqual(stats['threat_levels']['низкий']['count'], 30)
        self.assertAlmostEqual(stats['threat_levels']['низкий']['percent'], 60.0)
        self.assertEqual(stats['threat_levels']['средний']['count'], 10)
        self.assertEqual(stats['threat_levels']['высокий']['count'], 7)
        self.assertEqual(stats['threat_levels']['критический']['count'], 3)
        self.assertAlmostEqual(stats['average_energy_mt'], 2.3)
        self.assertEqual(stats['max_energy_mt'], 9.87)
        self.assertEqual(stats['high_threat_count'], 10)

    async def test_get_threats_by_asteroid_returns_list(self):
        items = [MagicMock(spec=ThreatAssessmentModel) for _ in range(2)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        result = await self.controller.get_threats_by_asteroid(self.session, asteroid_id=1001)

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()


if __name__ == '__main__':
    unittest.main()
