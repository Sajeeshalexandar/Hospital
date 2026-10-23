from django.contrib import admin
from .models import SubscriptionPlan, HospitalSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "currency", "duration_days", "max_users", "is_active")
    list_filter = ("is_active", "currency")
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(HospitalSubscription)
class HospitalSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("hospital", "plan", "status", "start_date", "end_date", "auto_renew")
    list_filter = ("status", "auto_renew", "plan")
    search_fields = ("hospital__name",)
    readonly_fields = ("created_at", "updated_at")
