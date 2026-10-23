from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ── Django built-in Admin (Super Admin raw DB management) ──────────────
    path("admin/", admin.site.urls),

    # ── Accounts: login & logout ────────────────────────────────────────────
    path("", include("accounts.urls")),

    # ── All dashboards (dispatcher + role-specific) ─────────────────────────
    path("", include("dashboards.urls")),

    # ── Hospitals app (Super Admin CRUD + Hospital Admin profile/settings) ──
    path("", include("hospitals.urls")),

    # ── Departments app (Hospital Admin CRUD) ───────────────────────────────
    path("", include("departments.urls")),

    # ── Subscriptions app (Super Admin plans & subscriptions) ───────────────
    path("", include("subscriptions.urls")),

    # ── Doctors app (Roster, schedules, availability) ───────────────────────
    path("", include("doctors.urls")),

    # ── Staff app (Staff, receptionists, nurses) ────────────────────────────
    path("", include("staff.urls")),

    # ── Patients app (Patient directory & registration) ─────────────────────
    path("", include("patients.urls")),

    # ── Appointments app (Scheduling, calendar, conflict validation) ───────
    path("", include("appointments.urls")),

    # ── Medical Records app (Clinical history, diagnosis notes) ────────────
    path("", include("medical_records.urls")),

    # ── Prescriptions app (Medications, digital prescriptions) ──────────────
    path("", include("prescriptions.urls")),

    # ── Laboratory app (Test orders & diagnostic reports) ───────────────────
    path("", include("laboratory.urls")),

    # ── Billing app (Invoices, items, payments) ─────────────────────────────
    path("", include("billing.urls")),

    # ── Notifications app (In-app alerts) ───────────────────────────────────
    path("", include("notifications.urls")),

    # ── Audit Logs app (Security & transactional audit trail) ───────────────
    path("", include("audit_logs.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
