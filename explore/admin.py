from django.contrib import admin
from .models import AIUsageEvent, Country

# Register your models here.
admin.site.register(Country)


@admin.register(AIUsageEvent)
class AIUsageEventAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'service',
        'model',
        'input_tokens',
        'output_tokens',
        'estimated_cost_usd',
        'created_at',
    )
    list_filter = ('service', 'model', 'created_at')
    search_fields = ('user__username', 'user__email', 'request_hash')
    readonly_fields = (
        'user',
        'service',
        'model',
        'request_hash',
        'input_tokens',
        'cached_input_tokens',
        'output_tokens',
        'estimated_cost_usd',
        'created_at',
    )
