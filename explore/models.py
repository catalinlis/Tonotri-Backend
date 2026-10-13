from django.db import models
from django.conf import settings

class Country(models.Model):
    alpha2 = models.CharField(max_length=10)
    alpha3 = models.CharField(max_length=10)
    country_name = models.CharField(max_length=100)


class AIUsageEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_events',
    )
    service = models.CharField(max_length=50, db_index=True)
    model = models.CharField(max_length=50)
    request_hash = models.CharField(max_length=64, db_index=True)
    input_tokens = models.PositiveIntegerField(default=0)
    cached_input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=12, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
