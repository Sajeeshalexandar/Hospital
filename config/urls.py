from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import custom role-specific admin sites
from config.admin_sites import (
    super_admin_site,
    hospital_admin_site,
    doctor_admin_site,
    receptionist_admin_site,
)

urlpatterns = [
    # ── Public Patient Website & Landing Page (Root) ────────────────────────
    path("", include("website.urls")),

    # ── Role-specific Django Admin Panels ──────────────────────────────────
    path("admin/super/", super_admin_site.urls),
    path("admin/hospital/", hospital_admin_site.urls),
    path("admin/doctor/", doctor_admin_site.urls),
    path("admin/receptionist/", receptionist_admin_site.urls),

    # ── Django Built-in Super Admin Panel (Raw DB Management) ───────────────
    path("admin/", admin.site.urls),

    # ── Accounts: Auth, Dedicated Role Logins, Logout ───────────────────────
    path("", include("accounts.urls")),

    # ── Dashboards (Smart Dispatcher + Role-Specific Dashboards) ───────────
    path("", include("dashboards.urls")),

    # ── Core Multi-Tenant Hospital Modules ─────────────────────────────────
    path("", include("hospitals.urls")),
    path("", include("departments.urls")),
    path("", include("subscriptions.urls")),
    path("", include("doctors.urls")),
    path("", include("staff.urls")),
    path("", include("patients.urls")),
    path("", include("appointments.urls")),
    path("", include("medical_records.urls")),
    path("", include("prescriptions.urls")),
    path("", include("laboratory.urls")),
    path("", include("billing.urls")),
    path("", include("notifications.urls")),
    path("", include("audit_logs.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
