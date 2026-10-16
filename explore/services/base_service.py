import json

from django.conf import settings

from .ai_cache import AIDescriptionCache, AIUsageTracker

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
        request_hash = self.cache.request_hash(self.service_name, parameters)
        cached = self.cache.get(request_hash)
        if cached is not None:
            return {'success': True, 'message': cached, 'cached': True}

        result = self.client.generate_json(model=model, prompt=prompt, schema=schema)
        # Backwards compatibility keeps simple fake clients useful in unit tests.
        raw = result if isinstance(result, str) else result.output_text
        message = json.loads(raw)

        if not isinstance(result, str):
            AIUsageTracker.record(
                user=user,
                service=self.service_name,
                model=model,
                request_hash=request_hash,
                result=result,
            )

        self.cache.set(request_hash, message)
        return {'success': True, 'message': message, 'cached': False}

