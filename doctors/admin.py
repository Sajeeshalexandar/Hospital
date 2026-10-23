from django.contrib import admin
from .models import DoctorProfile, DoctorAvailability


class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 0


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("__str__", "hospital", "department", "specialization", "is_active")
    list_filter = ("is_active", "hospital", "department")
    search_fields = ("user__email", "user__first_name", "user__last_name", "employee_code", "specialization")
    inlines = [DoctorAvailabilityInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("doctor", "get_weekday_display", "start_time", "end_time", "is_active")
    list_filter = ("weekday", "is_active")
