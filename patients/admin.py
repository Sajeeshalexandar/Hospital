from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("patient_id_code", "hospital", "gender", "blood_group", "contact_number", "is_active")
    list_filter = ("is_active", "hospital", "gender", "blood_group")
    search_fields = ("patient_id_code", "contact_number", "hospital__name")
    readonly_fields = ("created_at", "updated_at")
