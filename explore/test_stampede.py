"""Stampede coordination tests without external Redis or OpenAI calls."""

from concurrent.futures import ThreadPoolExecutor
from threading import Condition, Event, Thread, get_ident
from unittest.mock import Mock, patch

import redis
from django.test import SimpleTestCase, override_settings

from .services.ai_cache import AIDescriptionCache
from .services.exceptions import AIDescriptionUnavailable
from .services.explore_service import CityDescriptionService, CountryDescriptionService


class SharedRedis:
    """Thread-safe Redis substitute for contention, not Redis TTL semantics."""

    def __init__(self):
        self.condition = Condition()
        self.values = {}
        self.owners = {}
        self.contenders = set()

    def get(self, key):
        with self.condition:
            return self.values.get(key)

    def setex(self, key, ttl, value):
        with self.condition:
            self.values[key] = value

    def lock(self, key, *, timeout, thread_local):
        return SharedLock(self, key)


class SharedLock:
    def __init__(self, redis_client, key):
        self.redis = redis_client
        self.key = key
        self.token = object()

    def acquire(self, blocking):
        assert blocking is False
        with self.redis.condition:
            self.redis.contenders.add(get_ident())
            self.redis.condition.notify_all()
            if self.key in self.redis.owners:
                return False
            self.redis.owners[self.key] = self.token
            return True

    def owned(self):
        with self.redis.condition:
            return self.redis.owners.get(self.key) is self.token

    def extend(self, ttl, replace_ttl):
        return self.owned()

    def release(self):
        with self.redis.condition:
            if not self.owned():
                raise redis.exceptions.LockNotOwnedError('Lease lost')
            del self.redis.owners[self.key]


@override_settings(
    OPENAI_DESCRIPTION_MODEL='test-model',
    AI_DESCRIPTION_PROMPT_VERSION=1,
    AI_DESCRIPTION_LOCK_TTL=30,
    AI_DESCRIPTION_LOCK_WAIT=10,
    AI_DESCRIPTION_CACHE_TTL=60,
)
class StampedeProtectionTests(SimpleTestCase):
    def test_three_city_and_three_country_requests_generate_once_per_key(self):
        shared = SharedRedis()
        finish_generation = Event()
        city_started = Event()
        country_started = Event()

        def generate(started, result):
            started.set()
            if not finish_generation.wait(5):
                raise AssertionError('Test did not release generation')
            return result

        city_client = Mock()
        city_client.generate_json.side_effect = lambda **kwargs: generate(
            city_started, '{"city": "Bucharest"}',
        )
        country_client = Mock()
        country_client.generate_json.side_effect = lambda **kwargs: generate(
            country_started, '{"country": "Romania"}',
        )

        # Separate service/cache instances share only the Redis substitute.
        with ThreadPoolExecutor(max_workers=6) as pool:
            try:
                city_futures = [
                    pool.submit(
                        CityDescriptionService(
                            client=city_client, cache=AIDescriptionCache(shared),
                        ).generate,
                        city, 'Romania', 1000000,
                    )
                    for city in ['Bucharest', ' BUCHAREST ', 'bucharest']
                ]
                country_futures = [
                    pool.submit(
                        CountryDescriptionService(
                            client=country_client, cache=AIDescriptionCache(shared),
                        ).generate,
                        country,
                    )
                    for country in ['Romania', ' ROMANIA ', 'romania']
                ]
                self.assertTrue(city_started.wait(3), 'City leader did not start')
                self.assertTrue(country_started.wait(3), 'Country leader was blocked')
                with shared.condition:
                    self.assertTrue(shared.condition.wait_for(
                        lambda: len(shared.contenders) == 6, timeout=3,
                    ), 'Not all requests attempted acquisition')
                    self.assertEqual(len(shared.owners), 2)
            finally:
                finish_generation.set()

            for futures, message in [
                (city_futures, {'city': 'Bucharest'}),
                (country_futures, {'country': 'Romania'}),
            ]:
                results = [future.result(timeout=5) for future in futures]
                self.assertTrue(all(result['success'] for result in results))
                self.assertTrue(all(result['message'] == message for result in results))
                self.assertEqual(sum(not result['cached'] for result in results), 1)

        city_client.generate_json.assert_called_once()
        country_client.generate_json.assert_called_once()
        self.assertEqual(shared.owners, {})

    def make_service(self, redis_client):
        client = Mock()
        client.generate_json.return_value = '{"country": "Romania"}'
        return CountryDescriptionService(
            client=client, cache=AIDescriptionCache(redis_client),
        )

    @override_settings(AI_DESCRIPTION_LOCK_WAIT=0)
    def test_follower_times_out_without_generating_or_releasing_leaders_lock(self):
        client = Mock()
        client.get.return_value = None
        client.lock.return_value.acquire.return_value = False
        service = self.make_service(client)

        with self.assertRaises(AIDescriptionUnavailable):
            service.generate('Romania')

        service.client.generate_json.assert_not_called()
        client.setex.assert_not_called()
        client.lock.return_value.release.assert_not_called()

    def test_rechecks_cache_after_acquiring_lock(self):
        client = Mock()
        client.get.side_effect = [None, '{"country": "Romania"}']
        service = self.make_service(client)

        result = service.generate('Romania')

        self.assertTrue(result['cached'])
        service.client.generate_json.assert_not_called()
        client.lock.return_value.release.assert_called_once()

    def test_lost_ownership_prevents_publishing_generated_result(self):
        client = Mock()
        client.get.return_value = None
        client.lock.return_value.owned.side_effect = [True, False]
        service = self.make_service(client)

        with self.assertRaises(AIDescriptionUnavailable):
            service.generate('Romania')

        service.client.generate_json.assert_called_once()
        client.setex.assert_not_called()

    def test_acquisition_error_prevents_generation(self):
        client = Mock()
        client.get.return_value = None
        client.lock.return_value.acquire.side_effect = redis.ConnectionError()
        service = self.make_service(client)

        with self.assertRaises(AIDescriptionUnavailable):
            service.generate('Romania')

        service.client.generate_json.assert_not_called()
        client.setex.assert_not_called()


@override_settings(AI_DESCRIPTION_LOCK_TTL=0.03)
class RenewableLockTests(SimpleTestCase):
    def setUp(self):
        self.client = Mock()
        self.lock = self.client.lock.return_value
        self.cache = AIDescriptionCache(self.client)

    def test_renews_lease_and_stops_before_releasing(self):
        renewed = Event()
        workers = []

        def create_worker(**kwargs):
            worker = Thread(**kwargs)
            workers.append(worker)
            return worker

        def release():
            self.assertFalse(workers[0].is_alive())

        def extend(*args, **kwargs):
            renewed.set()
            return True

        self.lock.extend.side_effect = extend
        self.lock.release.side_effect = release
        with patch('explore.services.ai_cache.Thread', side_effect=create_worker):
            with self.cache.generation_lock('request') as ensure_owned:
                self.assertTrue(renewed.wait(3), 'Renewal did not run')
                ensure_owned()
                self.lock.release.assert_not_called()

        self.lock.extend.assert_called_with(0.03, replace_ttl=True)
        self.lock.release.assert_called_once()
        self.client.lock.assert_called_once_with(
            'ai_description:v1:lock:request', timeout=0.03, thread_local=False,
        )

    def test_failed_renewal_is_reported_by_ownership_check(self):
        for failure in [False, redis.ConnectionError('Redis unavailable')]:
            with self.subTest(failure=failure):
                stopped, lost = Event(), Event()
                self.lock.extend.side_effect = (
                    failure if isinstance(failure, Exception) else None
                )
                self.lock.extend.return_value = False
                with patch('explore.services.ai_cache.Event', side_effect=[stopped, lost]):
                    with self.cache.generation_lock('request') as ensure_owned:
                        self.assertTrue(lost.wait(3), 'Renewal failure was not signalled')
                        with self.assertRaises(AIDescriptionUnavailable):
                            ensure_owned()

    def test_ownership_query_error_is_unavailable(self):
        self.lock.owned.side_effect = redis.ConnectionError()
        with self.cache.generation_lock('request') as ensure_owned:
            with self.assertRaises(AIDescriptionUnavailable):
                ensure_owned()

    def test_exception_in_with_block_still_releases_lock(self):
        with self.assertRaisesRegex(ValueError, 'generation failed'):
            with self.cache.generation_lock('request'):
                raise ValueError('generation failed')
        self.lock.release.assert_called_once()

    def test_release_error_does_not_discard_completed_result(self):
        self.lock.release.side_effect = redis.ConnectionError()

        def complete_work():
            with self.cache.generation_lock('request') as ensure_owned:
                ensure_owned()
                return 'completed'

        with self.assertLogs('explore.services.ai_cache', level='WARNING'):
            self.assertEqual(complete_work(), 'completed')
