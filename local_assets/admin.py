from django.contrib import admin
from .models import LocalAsset


@admin.register(LocalAsset)
class LocalAssetAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "mac_address", "hostname", "person_name", "department", "device_type", "created_at")
    list_filter = ("device_type", "department")
    search_fields = ("ip_address", "mac_address", "person_name", "department", "hostname")
    list_per_page = 50
    ordering = ("ip_address",)
