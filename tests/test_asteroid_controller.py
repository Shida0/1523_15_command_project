import asyncio
import logging
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from controllers.asteroid_controller import AsteroidController
from models.asteroid import AsteroidModel


# Silence logger output during tests
logging.getLogger('controllers.asteroid_controller').setLevel(logging.CRITICAL)


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


class TestAsteroidController(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.controller = AsteroidController()
        self.session = AsyncMock()
        # Provide commit and rollback to be awaited
        self.session.commit = AsyncMock()
        self.session.rollback = AsyncMock()

    async def test_get_by_mpc_number_found(self):
        asteroid = MagicMock(spec=AsteroidModel)
        asteroid.name = 'Apophis'
        self.session.execute = AsyncMock(return_value=FakeScalarResult(asteroid))

        result = await self.controller.get_by_mpc_number(self.session, 99942)

        self.assertIs(result, asteroid)
        self.session.execute.assert_awaited()

    async def test_get_by_mpc_number_not_found(self):
        self.session.execute = AsyncMock(return_value=FakeScalarResult(None))

        result = await self.controller.get_by_mpc_number(self.session, 123456)

        self.assertIsNone(result)
        self.session.execute.assert_awaited()

    async def test_get_pha_asteroids_returns_list(self):
        items = [MagicMock(spec=AsteroidModel), MagicMock(spec=AsteroidModel)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        result = await self.controller.get_pha_asteroids(self.session, skip=0, limit=10)

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()

    async def test_search_by_name_returns_list(self):
        items = [MagicMock(spec=AsteroidModel)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        result = await self.controller.search_by_name(self.session, 'Apo', skip=0, limit=50)

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()

    async def test_bulk_create_creates_updates_and_commits_and_skips_missing(self):
        data = [
            {'mpc_number': None, 'name': 'NoMPC'},  # should be skipped
            {'mpc_number': 1, 'name': 'NewOne'},    # create
            {'mpc_number': 2, 'name': 'Existing'},  # update
        ]

        # Patch the helper calls to isolate logic
        with patch.object(self.controller, 'get_by_mpc_number', new=AsyncMock(side_effect=[None, MagicMock(spec=AsteroidModel)])) as mocked_get,\
             patch.object(self.controller, 'create', new=AsyncMock()) as mocked_create,\
             patch.object(self.controller, 'update', new=AsyncMock()) as mocked_update:

            created, updated = await self.controller.bulk_create(self.session, data)

            self.assertEqual(created, 1)
            self.assertEqual(updated, 1)
            # get_by_mpc_number called only for items with mpc_number
            self.assertEqual(mocked_get.await_count, 2)
            mocked_create.assert_awaited_once()
            mocked_update.assert_awaited_once()
            self.session.commit.assert_awaited_once()

    async def test_bulk_create_rollback_on_exception(self):
        data = [{'mpc_number': 42, 'name': 'Boom'}]

        with patch.object(self.controller, 'get_by_mpc_number', new=AsyncMock(return_value=None)), \
             patch.object(self.controller, 'create', new=AsyncMock(side_effect=RuntimeError('fail'))):

            with self.assertRaises(RuntimeError):
                await self.controller.bulk_create(self.session, data)

            self.session.rollback.assert_awaited_once()
            self.session.commit.assert_not_awaited()

    async def test_get_asteroids_by_diameter_range_filters(self):
        items = [MagicMock(spec=AsteroidModel) for _ in range(3)]
        self.session.execute = AsyncMock(return_value=FakeResult(scalars_list=items))

        result = await self.controller.get_asteroids_by_diameter_range(
            self.session,
            min_diameter=0.1,
            max_diameter=10.0,
            skip=5,
            limit=3,
        )

        self.assertEqual(result, items)
        self.session.execute.assert_awaited()

    async def test_get_statistics_computation(self):
        # total, pha_count, avg_diameter, min_moid
        side_effects = [
            FakeScalarResult(100),
            FakeScalarResult(25),
            FakeScalarResult(1.23456),
            FakeScalarResult(0.001),
        ]
        self.session.execute = AsyncMock(side_effect=side_effects)

        stats = await self.controller.get_statistics(self.session)

        self.assertEqual(stats['total_asteroids'], 100)
        self.assertEqual(stats['pha_count'], 25)
        self.assertAlmostEqual(stats['percent_pha'], 25.0)
        self.assertAlmostEqual(stats['average_diameter_km'], 1.23)
        self.assertEqual(stats['min_moid_au'], 0.001)
        self.assertIn('last_updated', stats)


if __name__ == '__main__':
    unittest.main()
