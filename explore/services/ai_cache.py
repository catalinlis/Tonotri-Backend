import hashlib
import json
import logging
from contextlib import contextmanager
from decimal import Decimal
from threading import Event, Thread

import redis
from django.conf import settings

from explore.models import AIUsageEvent
from .exceptions import AIDescriptionUnavailable

logger = logging.getLogger(__name__)


class AIDescriptionCache:
    """Cache descriptions and coordinate generation through shared Redis."""

    PREFIX = 'ai_description:v1'

    def __init__(self, client=None):
        self.client = client or redis.Redis(
            host=settings.REDIS_CONFIG['HOST'],
            port=settings.REDIS_CONFIG['PORT'],
            db=settings.REDIS_CONFIG['DB'],
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
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
        """Distinguish an ordinary cache miss from unavailable coordination."""

        try:
            cached = self.client.get(f'{self.PREFIX}:{request_hash}')
        except redis.RedisError as exc:
            raise AIDescriptionUnavailable() from exc
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
            raise AIDescriptionUnavailable() from exc

    @contextmanager
    def generation_lock(self, request_hash):
        """Try once, without waiting, to lock generation for this request hash.

        Yield None if another worker holds the Redis lock. The caller must
        check for None before generating; the with block still runs.

        If acquired, renew the lock's TTL in a background thread and yield
        an ensure_owned callback. Calling it checks that this worker's token
        still owns the Redis lock, raising AIDescriptionUnavailable if renewal
        failed or ownership cannot be confirmed. It checks lock ownership,
        not thread ownership, and does not make subsequent writes atomic.

        On exit, including exceptions, stop renewal, wait for the thread, and
        attempt to release the lock. Release errors are logged; any remaining
        lease expires. Redis errors during acquisition raise
        AIDescriptionUnavailable.
        """
        lease = settings.AI_DESCRIPTION_LOCK_TTL
        lock = self.client.lock(
            f'{self.PREFIX}:lock:{request_hash}',
            timeout=lease,
            thread_local=False,
        )
        try:
            acquired = lock.acquire(blocking=False)
        except redis.RedisError as exc:
            raise AIDescriptionUnavailable() from exc
        if not acquired:
            yield None
            return

        stopped = Event()
        lost = Event()

        def renew():
            while not stopped.wait(lease / 3):
                try:
                    if not lock.extend(lease, replace_ttl=True):
                        lost.set()
                        return
                except redis.RedisError:
                    lost.set()
                    return

        def ensure_owned():
            try:
                if lost.is_set() or not lock.owned():
                    raise AIDescriptionUnavailable()
            except redis.RedisError as exc:
                raise AIDescriptionUnavailable() from exc

        worker = Thread(target=renew, name='ai-description-lock', daemon=True)
        try:
            worker.start()
            yield ensure_owned
        finally:
            stopped.set()
            if worker.ident is not None:
                worker.join()
            try:
                lock.release()
            except redis.RedisError:
                # Token-checked release cannot remove another worker's lease.
                # A completed result should still be returned if release fails.
                logger.warning('Could not release AI description lock, lease will expire.')


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
