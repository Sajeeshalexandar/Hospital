from django.contrib import admin
from .models import Hospital, HospitalTemplate, HospitalSettings


@admin.register(HospitalTemplate)
class HospitalTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "template_code")


class HospitalSettingsInline(admin.StackedInline):
    model = HospitalSettings
    can_delete = False
    extra = 0


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_number", "city", "state", "status", "created_at")
    list_filter = ("status", "country", "state")
    search_fields = ("name", "registration_number", "email", "city")
    inlines = [HospitalSettingsInline]
    readonly_fields = ("created_at", "updated_at")
