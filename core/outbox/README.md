# Outbox publishing

The existing Celery worker executes `core.outbox.publish_pending`. Celery Beat enqueues it every 10 seconds. Each task handles up to 100 events with fewer than 10 recorded attempts. Failed events are eligible on the next polling cycle, exhausted events remain unpublished for investigation and manual retry.

From the directory containing `manage.py`, run these in separate terminals:

```sh
celery -A TonotriBackend worker -l info -P solo
celery -A TonotriBackend beat -l info
```

Redis and the configured database must be available, and migrations must be applied. Docker Compose also defines the worker, Redis, and Beat services:

```sh
docker compose up -d --build redis celery celery-beat
```

Run only one Beat scheduler per deployment. Pending polling tasks expire after 10 seconds to avoid a backlog while workers are offline, later ticks still discover unpublished events. Task-level failures are retried by later ticks.

The publisher holds a database row lock during each SQS send. SQS delivery and the database commit are not atomic: consumers must tolerate duplicate `event_id` values. This worker publishes messages, the image-processing consumer remains a separate service.
