from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "hospital", "is_active", "created_at")
    list_filter = ("is_active", "hospital")
    search_fields = ("name", "hospital__name")
    readonly_fields = ("created_at", "updated_at")
