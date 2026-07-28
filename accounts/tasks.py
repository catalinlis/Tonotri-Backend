from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list):

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=recipient_list,
            fail_silently=False
        )

        logger.info(f"Email sent to {recipient_list}")

    except Exception as exc:
        logger.error(f"Email failed: {exc}")
        raise self.retry(exc=exc)
        
