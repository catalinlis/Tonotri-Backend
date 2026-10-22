import logging

import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def database_is_ready():
    """Return whether Django can execute a minimal database query."""

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return True
    except Exception:
        logger.exception('Database readiness check failed')
        return False


def redis_is_ready():
    """Return whether the optional Redis cache responds to a ping."""

    try:
        client = redis.Redis(
            host=settings.REDIS_CONFIG['HOST'],
            port=settings.REDIS_CONFIG['PORT'],
            db=settings.REDIS_CONFIG['DB'],
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        return bool(client.ping())
    except redis.RedisError:
        logger.warning('Redis readiness check failed', exc_info=True)
        return False


@never_cache
@require_GET
def liveness(request):
    """Confirm that the Django process can serve HTTP requests."""

    return JsonResponse({'status': 'healthy'})


@never_cache
@require_GET
def readiness(request):
    """Report required and optional dependency availability."""

    database_ready = database_is_ready()
    redis_ready = redis_is_ready()

    if not database_ready:
        overall_status = 'unhealthy'
        status_code = 503
    elif not redis_ready:
        overall_status = 'degraded'
        status_code = 200
    else:
        overall_status = 'healthy'
        status_code = 200

    return JsonResponse(
        {
            'status': overall_status,
            'services': {
                'database': 'healthy' if database_ready else 'unavailable',
                'redis': 'healthy' if redis_ready else 'unavailable',
            },
        },
        status=status_code,
    )
