from django.contrib import admin
from .models import IdempotencyRecord

@admin.register(IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):
    list_display = ("scope", "key", "user_id", "response_status", "created_at")
    list_filter = ("scope",)
    search_fields = ("key", "user_id")
    readonly_fields = ("request_hash", "response_status", "response_body", "created_at")
    date_hierarchy = "created_at"