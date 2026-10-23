from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "department", "hospital", "start_at", "end_at", "status")
    list_filter = ("status", "hospital", "department")
    search_fields = ("patient__patient_id_code", "doctor__user__email", "hospital__name")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_at"
