from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("__str__", "hospital", "job_title", "employee_code", "is_active", "date_of_joining")
    list_filter = ("is_active", "hospital")
    search_fields = ("user__email", "user__first_name", "user__last_name", "employee_code", "job_title")
    readonly_fields = ("created_at", "updated_at")
