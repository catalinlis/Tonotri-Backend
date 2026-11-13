from celery import shared_task


@shared_task(name='core.outbox.publish_pending', ignore_result=True)
def publish_pending(batch_size=100, max_attempts=10):
    """Publish one batch; subsequent Beat ticks retry pending events."""
    from .publisher import OutboxPublisher

    return OutboxPublisher(max_attempts=max_attempts).publish_pending(
        batch_size=batch_size,
    )
