import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import redis
from django.test import SimpleTestCase, TestCase, override_settings
from users.models import User
from .clients.openai_client import GeneratedJSON
from .models import AIUsageEvent
from .serializers import LandmarkDescriptionQuerySerializer
from .services.ai_cache import AIDescriptionCache, AIUsageTracker
from .services.explore_service import CountryDescriptionService
from .services.photo_cache import UnsplashPhotoCache
from .services.photo_service import LocationPhotoService


class ExploreSerializerTests(SimpleTestCase):
    def test_landmark_description_uses_country_field(self):
        serializer = LandmarkDescriptionQuerySerializer(
            data={
                "landmark": "Colosseum",
                "city": "Rome",
                "country": "Italy",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["country"], "Italy")


class MemoryCache:
    def __init__(self):
        self.values = {}

    def request_hash(self, service, parameters):
        return AIDescriptionCache.request_hash(service, parameters)

    def get(self, request_hash):
        return self.values.get(request_hash)

    def set(self, request_hash, value):
        self.values[request_hash] = value


class FakeOpenAIClient:
    def __init__(self):
        self.calls = 0

    def generate_json(self, **kwargs):
        self.calls += 1
        return GeneratedJSON(
            output_text=json.dumps({"country": "Romania"}),
            input_tokens=1000,
            cached_input_tokens=200,
            output_tokens=500,
        )


class MemoryPhotoCache:
    def __init__(self):
        self.values = {}

    def request_hash(self, query, photo_count):
        return UnsplashPhotoCache.request_hash(query, photo_count)

    def get(self, request_hash):
        return self.values.get(request_hash)

    def set(self, request_hash, value):
        self.values[request_hash] = value


class FakeUnsplashClient:
    def __init__(self, urls):
        self.urls = urls
        self.calls = 0

    def search_photo_urls(self, query, per_page):
        self.calls += 1
        return self.urls


class LocationPhotoCachingTests(SimpleTestCase):
    def test_reuses_cached_urls_for_equivalent_location_queries(self):
        client = FakeUnsplashClient([f'https://example.com/{index}' for index in range(6)])
        cache = MemoryPhotoCache()
        service = LocationPhotoService(
            client=client,
            cache=cache,
            sampler=lambda urls, count: urls[:count],
        )

        first = service.get_photo_urls('Bucharest Romania')
        second = service.get_photo_urls('  BUCHAREST   romania ')

        self.assertEqual(first, client.urls[:5])
        self.assertEqual(second, first)
        self.assertEqual(client.calls, 1)

    def test_caches_empty_result_when_fewer_than_five_photos_exist(self):
        client = FakeUnsplashClient(['https://example.com/1'])
        service = LocationPhotoService(client=client, cache=MemoryPhotoCache())

        self.assertEqual(service.get_photo_urls('Small place'), [])
        self.assertEqual(service.get_photo_urls('Small place'), [])
        self.assertEqual(client.calls, 1)


@override_settings(
    AI_DESCRIPTION_CACHE_TTL=86400,
    UNSPLASH_PHOTO_CACHE_TTL=86400,
)
class RedisCacheFailureTests(SimpleTestCase):
    def test_ai_cache_treats_redis_failure_as_a_cache_miss(self):
        client = Mock()
        client.get.side_effect = redis.ConnectionError('Redis is unavailable')
        cache = AIDescriptionCache(client=client)

        self.assertIsNone(cache.get('request-hash'))

    def test_ai_cache_ignores_redis_failure_when_saving(self):
        client = Mock()
        client.setex.side_effect = redis.ConnectionError('Redis is unavailable')
        cache = AIDescriptionCache(client=client)

        cache.set('request-hash', {'country': 'Romania'})

    @override_settings(OPENAI_DESCRIPTION_MODEL='gpt-5-mini')
    def test_ai_service_continues_when_redis_is_unavailable(self):
        redis_client = Mock()
        redis_client.get.side_effect = redis.ConnectionError('Redis is unavailable')
        redis_client.setex.side_effect = redis.ConnectionError('Redis is unavailable')
        ai_client = FakeOpenAIClient()
        service = CountryDescriptionService(
            client=ai_client,
            cache=AIDescriptionCache(client=redis_client),
        )

        result = service.generate('Romania')

        self.assertTrue(result['success'])
        self.assertFalse(result['cached'])
        self.assertEqual(result['message'], {'country': 'Romania'})
        self.assertEqual(ai_client.calls, 1)

    def test_photo_cache_treats_redis_failure_as_a_cache_miss(self):
        client = Mock()
        client.get.side_effect = redis.ConnectionError('Redis is unavailable')
        cache = UnsplashPhotoCache(client=client)

        self.assertIsNone(cache.get('request-hash'))

    def test_photo_cache_ignores_redis_failure_when_saving(self):
        client = Mock()
        client.setex.side_effect = redis.ConnectionError('Redis is unavailable')
        cache = UnsplashPhotoCache(client=client)

        cache.set('request-hash', ['https://example.com/photo'])


@override_settings(
    OPENAI_DESCRIPTION_MODEL='gpt-5-mini',
    OPENAI_INPUT_PRICE_PER_MILLION='0.25',
    OPENAI_CACHED_INPUT_PRICE_PER_MILLION='0.025',
    OPENAI_OUTPUT_PRICE_PER_MILLION='2.00',
)
class AIDescriptionCachingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cache_user',
            email='cache@example.com',
            password='StrongPass1',
            birthday=date(1990, 1, 1),
        )
        self.client = FakeOpenAIClient()
        self.cache = MemoryCache()
        self.service = CountryDescriptionService(
            client=self.client,
            cache=self.cache,
        )

    def test_cache_miss_records_usage_and_cost(self):
        result = self.service.generate('Romania', user=self.user)

        self.assertTrue(result['success'])
        self.assertFalse(result['cached'])
        self.assertEqual(self.client.calls, 1)

        usage = AIUsageEvent.objects.get(user=self.user)
        self.assertEqual(usage.input_tokens, 1000)
        self.assertEqual(usage.cached_input_tokens, 200)
        self.assertEqual(usage.output_tokens, 500)
        self.assertEqual(usage.estimated_cost_usd, Decimal('0.00120500'))

    def test_cache_hit_does_not_call_openai_or_record_more_cost(self):
        first = self.service.generate('Romania', user=self.user)
        second = self.service.generate('  ROMANIA ', user=self.user)

        self.assertFalse(first['cached'])
        self.assertTrue(second['cached'])
        self.assertEqual(self.client.calls, 1)
        self.assertEqual(AIUsageEvent.objects.filter(user=self.user).count(), 1)

    def test_cost_calculation_clamps_cached_tokens_to_input_tokens(self):
        cost = AIUsageTracker.calculate_cost(
            input_tokens=100,
            cached_input_tokens=200,
            output_tokens=0,
        )

        self.assertEqual(cost, Decimal('0.0000025'))
