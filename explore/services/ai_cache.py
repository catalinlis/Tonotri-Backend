import hashlib
import json
from decimal import Decimal

import redis
from django.conf import settings

from explore.models import AIUsageEvent


class AIDescriptionCache:
    PREFIX = 'ai_description:v1'

    def __init__(self, client=None):
        self.client = client or redis.Redis(
            host=settings.REDIS_CONFIG['HOST'],
            port=settings.REDIS_CONFIG['PORT'],
            db=settings.REDIS_CONFIG['DB'],
            decode_responses=True,
        )

    @staticmethod
    def request_hash(service, parameters):
        canonical = json.dumps(
            {'service': service, 'parameters': parameters},
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def get(self, request_hash):
        cached = self.client.get(f'{self.PREFIX}:{request_hash}')
        return json.loads(cached) if cached is not None else None

    def set(self, request_hash, value):
        self.client.setex(
            f'{self.PREFIX}:{request_hash}',
            settings.AI_DESCRIPTION_CACHE_TTL,
            json.dumps(value, separators=(',', ':')),
        )


class AIUsageTracker:
    MILLION = Decimal('1000000')

    @classmethod
    def calculate_cost(cls, input_tokens, cached_input_tokens, output_tokens):
        cached_input_tokens = min(cached_input_tokens, input_tokens)
        uncached_input_tokens = input_tokens - cached_input_tokens
        return (
            Decimal(uncached_input_tokens) * Decimal(settings.OPENAI_INPUT_PRICE_PER_MILLION)
            + Decimal(cached_input_tokens) * Decimal(settings.OPENAI_CACHED_INPUT_PRICE_PER_MILLION)
            + Decimal(output_tokens) * Decimal(settings.OPENAI_OUTPUT_PRICE_PER_MILLION)
        ) / cls.MILLION

    @classmethod
    def record(cls, *, user, service, model, request_hash, result):
        if user is None or not getattr(user, 'is_authenticated', False):
            return None

        cost = cls.calculate_cost(
            result.input_tokens,
            result.cached_input_tokens,
            result.output_tokens,
        )
        return AIUsageEvent.objects.create(
            user=user,
            service=service,
            model=model,
            request_hash=request_hash,
            input_tokens=result.input_tokens,
            cached_input_tokens=result.cached_input_tokens,
            output_tokens=result.output_tokens,
            estimated_cost_usd=cost,
        )
