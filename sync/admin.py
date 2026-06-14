from django.contrib import admin
from .models import SourceFeed, SourceRecord


@admin.register(SourceFeed)
class SourceFeedAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "feed_type", "is_active", "last_sync_status", "last_sync_at", "consecutive_failures")
    list_filter = ("feed_type", "is_active", "last_sync_status")
    search_fields = ("name", "slug", "description")
    list_per_page = 50


@admin.register(SourceRecord)
class SourceRecordAdmin(admin.ModelAdmin):
    list_display = ("source", "sync_type", "status", "total_count", "new_count", "started_at")
    list_filter = ("status", "sync_type")
    date_hierarchy = "started_at"
