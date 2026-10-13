import json
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase, TestCase, override_settings

from users.models import User

from .clients.openai_client import GeneratedJSON
from .models import AIUsageEvent
from .serializers import LandmarkDescriptionQuerySerializer
from .services.ai_cache import AIDescriptionCache, AIUsageTracker
from .services.explore_service import CountryDescriptionService


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
