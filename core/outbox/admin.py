from django.contrib import admin

from .models import OutboxEvent

@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "created_at", "published_at", "attempts")
    list_filter = ("event_type", "published_at")
    search_fields = ("id", "event_type")
    readonly_fields = ("id", "created_at", "published_at", "attempts")
    date_hierarchy = "created_at"
