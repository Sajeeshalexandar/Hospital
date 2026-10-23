from django.contrib import admin
from .models import HospitalMembership


@admin.register(HospitalMembership)
class HospitalMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active", "hospital")
    search_fields = ("user__email", "user__first_name", "user__last_name", "hospital__name")
    readonly_fields = ("joined_at", "created_at", "updated_at")
