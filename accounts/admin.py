from django.contrib import admin
from .models import AllowedIP


@admin.register(AllowedIP)
class AllowedIPAdmin(admin.ModelAdmin):
    list_display = ("cidr", "description", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("cidr", "description")
