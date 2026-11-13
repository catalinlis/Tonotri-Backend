import json
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from media.services import SQSService
from .models import OutboxEvent

logger = logging.getLogger(__name__)

class OutboxPublisher:

    def __init__(self, *, max_attempts=10):
        self.client = SQSService().client
        self.max_attempts = max_attempts
        self.queue_routes = {
            'image.process': settings.AWS_SQS_IMAGE_PROCESSING_URL,
        }

    def publish_pending(self, *, batch_size=100):
        # Snapshots candidates so a failed event is not retried repeatedly within this same batch
        event_ids = list(
            OutboxEvent.objects.filter(
                published_at__isnull=True,
                attempts__lt=self.max_attempts,
            )
            .order_by('created_at', 'id')
            .values_list('id', flat=True)[:batch_size]
        )

        published_count = 0

        for event_id in event_ids:
            if self._publish_one(event_id):
                published_count += 1

        return published_count

    def _publish_one(self, event_id):
        with transaction.atomic():
            event = (
                OutboxEvent.objects.select_for_update(skip_locked=True)
                .filter(
                    pk=event_id,
                    published_at__isnull=True,
                    attempts__lt=self.max_attempts
                )
                .first()
            )

            # Another publisher may have locked or published this event
            if event is None:
                return False

            event.attempts += 1

            try:
                queue_url = self.queue_routes[event.event_type]
                message = {
                    **event.payload,
                    'event': event.event_type,
                    'event_id': str(event.id)
                }

                self.client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(message)
                )

            except Exception:
                # Persist the failed attempt without marking it published.
                event.save(update_fields=['attempts'])
                logger.exception(
                    'Outbox publishing failed: event_id=%s attempt=%s',
                    event.id,
                    event.attempts
                )

                if event.attempts >= self.max_attempts:
                    logger.error(
                        'Outbox event exhausted automatic retries: %s',
                        event.id
                    )

                return False

            event.published_at = timezone.now()
            event.save(update_fields=['attempts', 'published_at'])
            return True
