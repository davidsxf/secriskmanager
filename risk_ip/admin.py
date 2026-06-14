from django.contrib import admin

from .models import MaliciousIP, SourcePreset, Tag


@admin.register(SourcePreset)
class SourcePresetAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_manual", "description")
    list_filter = ("is_manual",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "description")
    search_fields = ("name",)


@admin.register(MaliciousIP)
class MaliciousIPAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "cidr", "range_display", "source", "category", "confidence", "is_active", "created_at")
    list_filter = ("source", "category", "is_active")
    search_fields = ("ip_address", "cidr", "remark")
    list_per_page = 50

    def range_display(self, obj):
        if obj.range_start and obj.range_end:
            return f"{obj.range_start} - {obj.range_end}"
        return ""
    range_display.short_description = "IP 范围"
