from django.contrib import admin
from .models import MaliciousDomain


@admin.register(MaliciousDomain)
class MaliciousDomainAdmin(admin.ModelAdmin):
    list_display = ("domain_display", "source", "category", "is_active", "created_at")
    list_filter = ("source", "category", "is_active")
    search_fields = ("domain", "remark")
    list_per_page = 50

    def domain_display(self, obj):
        return f"@{obj.domain}" if obj.prefix_at else obj.domain
    domain_display.short_description = "域名"
