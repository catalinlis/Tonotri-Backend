import hashlib
import json
import logging

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class UnsplashPhotoCache:
    PREFIX = 'unsplash_photos:v1'

    def __init__(self, client=None):
        self.client = client or redis.Redis(
            host=settings.REDIS_CONFIG['HOST'],
            port=settings.REDIS_CONFIG['PORT'],
            db=settings.REDIS_CONFIG['DB'],
            decode_responses=True,
        )

    @staticmethod
    def request_hash(query, photo_count):
        canonical = json.dumps(
            {
                'query': ' '.join(query.casefold().split()),
                'photo_count': photo_count,
            },
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def get(self, request_hash):
        try:
            cached = self.client.get(f'{self.PREFIX}:{request_hash}')
        except redis.RedisError as exc:
            logger.warning('Photo cache is unavailable; continuing without it: %s', exc)
            return None
        return json.loads(cached) if cached is not None else None

    def set(self, request_hash, photo_urls):
        try:
            self.client.setex(
                f'{self.PREFIX}:{request_hash}',
                settings.UNSPLASH_PHOTO_CACHE_TTL,
                json.dumps(photo_urls, separators=(',', ':')),
            )
        except redis.RedisError as exc:
            logger.warning('Photo cache is unavailable; result was not cached: %s', exc)
