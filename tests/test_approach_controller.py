import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from controllers.approach_controller import ApproachController
from models.close_approach import CloseApproachModel


# Silence logger output during tests
logging.getLogger('controllers.approach_controller').setLevel(logging.CRITICAL)


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


class TestApproachController(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.controller = ApproachController()
        self.session = AsyncMock()
        # Provide commit, rollback, delete to be awaited
        self.session.commit = AsyncMock()
        self.session.rollback = AsyncMock()
        self.session.delete = AsyncMock()

    async def test_get_by_asteroid_returns_list(self):
        items = [MagicMock(spec=CloseApproachModel) for _ in range(3)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        result = await self.controller.get_by_asteroid(self.session, asteroid_id=123, skip=1, limit=3)

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()

    async def test_get_approaches_in_period_with_max_distance_and_pagination(self):
        items = [MagicMock(spec=CloseApproachModel) for _ in range(2)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        result = await self.controller.get_approaches_in_period(
            self.session,
            start_date=start,
            end_date=end,
            max_distance=0.5,
            skip=5,
            limit=2,
        )

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()

    async def test_bulk_create_approaches_create_update_skip_and_commit(self):
        now = datetime.utcnow()
        data = [
            # skipped (missing asteroid_id or approach_time)
            {'asteroid_id': None, 'approach_time': now},
            {'asteroid_id': 1, 'approach_time': now + timedelta(days=1), 'distance_au': 0.42},  # create
            {'asteroid_id': 2, 'approach_time': now + timedelta(days=2), 'distance_au': 0.13},  # update
        ]

        existing = MagicMock(spec=CloseApproachModel)
        existing.id = 999

        # First existence check -> None (create), second -> existing (update)
        self.session.execute = AsyncMock(side_effect=[
            FakeScalarResult(None),
            FakeScalarResult(existing),
        ])

        with patch.object(self.controller, 'create', new=AsyncMock()) as mocked_create, \
             patch.object(self.controller, 'update', new=AsyncMock()) as mocked_update:

            created_count = await self.controller.bulk_create_approaches(
                self.session,
                approaches_data=data,
                calculation_batch_id='batch-1'
            )

            # Only one new record created; existing one updated but not counted in created
            self.assertEqual(created_count, 1)
            mocked_create.assert_awaited_once()
            mocked_update.assert_awaited_once()
            self.session.commit.assert_awaited_once()

    async def test_bulk_create_approaches_rollback_on_exception(self):
        now = datetime.utcnow()
        data = [{'asteroid_id': 1, 'approach_time': now}]

        # Existence check says it's new
        self.session.execute = AsyncMock(return_value=FakeScalarResult(None))

        with patch.object(self.controller, 'create', new=AsyncMock(side_effect=RuntimeError('boom'))):
            with self.assertRaises(RuntimeError):
                await self.controller.bulk_create_approaches(self.session, data, calculation_batch_id='b2')

            self.session.rollback.assert_awaited_once()
            self.session.commit.assert_not_awaited()

    async def test_delete_old_approaches_deletes_and_commits(self):
        items = [MagicMock(spec=CloseApproachModel) for _ in range(4)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        cutoff = datetime.utcnow()
        deleted = await self.controller.delete_old_approaches(self.session, cutoff)

        self.assertEqual(deleted, len(items))
        # delete called for each item
        self.assertEqual(self.session.delete.await_count, len(items))
        self.session.commit.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
