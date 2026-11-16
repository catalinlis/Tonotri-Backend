import json
import logging
import random
import time

from django.conf import settings
from django.db import DatabaseError

from .ai_cache import AIDescriptionCache, AIUsageTracker
from .exceptions import AIDescriptionUnavailable

logger = logging.getLogger(__name__)

class BaseDescriptionAI:
    """Provide cached, tracked JSON generation for travel services."""

    service_name = None

    def __init__(self, client=None, cache=None):
        from explore.clients.openai_client import OpenAIClient

        self.client = client or OpenAIClient()
        self.cache = cache or AIDescriptionCache()

    def _generate_cached(self, *, parameters, prompt, schema, user=None):
        """Return cached output or generate, track, and cache a new result."""

        model = settings.OPENAI_DESCRIPTION_MODEL
        request_hash = self.cache.request_hash(self.service_name, {
            'parameters': parameters,
            'model': model,
            'version': settings.AI_DESCRIPTION_PROMPT_VERSION,
            'schema': schema,
        })
        deadline = time.monotonic() + settings.AI_DESCRIPTION_LOCK_WAIT
        while True:
            cached = self.cache.get(request_hash)
            if cached is not None:
                return {'success': True, 'message': cached, 'cached': True}

            with self.cache.generation_lock(request_hash) as ensure_owned:
                if ensure_owned is not None:
                    cached = self.cache.get(request_hash)
                    if cached is not None:
                        return {'success': True, 'message': cached, 'cached': True}
                    ensure_owned()
                    return self._generate_and_cache(
                        model, prompt, schema, user, request_hash, ensure_owned,
                    )

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AIDescriptionUnavailable()
            time.sleep(min(remaining, random.uniform(0.15, 0.3)))

    def _generate_and_cache(self, model, prompt, schema, user, request_hash, ensure_owned):
        result = self.client.generate_json(model=model, prompt=prompt, schema=schema)
        # Backwards compatibility keeps simple fake clients useful in unit tests.
        raw = result if isinstance(result, str) else result.output_text
        message = json.loads(raw)

        # Publish before accounting so an accounting failure cannot cause
        # another paid generation of a successfully cached description.
        try:
            ensure_owned()
            self.cache.set(request_hash, message)
        finally:
            self._record_usage(user, model, request_hash, result)
        return {'success': True, 'message': message, 'cached': False}

    def _record_usage(self, user, model, request_hash, result):
        if not isinstance(result, str):
            try:
                AIUsageTracker.record(
                    user=user,
                    service=self.service_name,
                    model=model,
                    request_hash=request_hash,
                    result=result,
                )
            except DatabaseError:
                # Do not mask a coordination 503 or discard a cached success.
                logger.error('Failed to persist AI usage for request %s.', request_hash)

