import hashlib
import json
import logging
from decimal import Decimal

import redis
from django.conf import settings

from explore.models import AIUsageEvent

logger = logging.getLogger(__name__)


class AIDescriptionCache:
    """Cache AI descriptions in Redis without making Redis mandatory."""

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
        """Build a stable cache key from normalized request parameters."""

        canonical = json.dumps(
            {'service': service, 'parameters': parameters},
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def get(self, request_hash):
        """Return cached content, or a cache miss when Redis is unavailable."""

        try:
            cached = self.client.get(f'{self.PREFIX}:{request_hash}')
        except redis.RedisError as exc:
            logger.warning('AI cache is unavailable; continuing without it: %s', exc)
            return None
        return json.loads(cached) if cached is not None else None

    def set(self, request_hash, value):
        """Cache generated content when Redis is available."""

        try:
            self.client.setex(
                f'{self.PREFIX}:{request_hash}',
                settings.AI_DESCRIPTION_CACHE_TTL,
                json.dumps(value, separators=(',', ':')),
            )
        except redis.RedisError as exc:
            logger.warning('AI cache is unavailable; result was not cached: %s', exc)


class AIUsageTracker:
    """Calculate and persist per-user OpenAI usage costs."""

    MILLION = Decimal('1000000')

    @classmethod
    def calculate_cost(cls, input_tokens, cached_input_tokens, output_tokens):
        """Estimate request cost from configured per-token prices."""

        cached_input_tokens = min(cached_input_tokens, input_tokens)
        uncached_input_tokens = input_tokens - cached_input_tokens
        return (
            Decimal(uncached_input_tokens) * Decimal(settings.OPENAI_INPUT_PRICE_PER_MILLION)
            + Decimal(cached_input_tokens) * Decimal(settings.OPENAI_CACHED_INPUT_PRICE_PER_MILLION)
            + Decimal(output_tokens) * Decimal(settings.OPENAI_OUTPUT_PRICE_PER_MILLION)
        ) / cls.MILLION

    @classmethod
    def record(cls, *, user, service, model, request_hash, result):
        """Persist usage for authenticated users."""

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
