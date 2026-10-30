from django.urls import path
from . import views

urlpatterns = [
    # ── Landing Page (Patients Website) ────────────────────────────────────
    path("", views.landing_page, name="landing"),

    # ── Online Appointment Booking ─────────────────────────────────────────
    path("book-appointment/", views.book_appointment, name="book_appointment"),

    # ── Patient Self-Service Portal ────────────────────────────────────────
    path("patient-portal/", views.patient_portal, name="patient_portal"),

    # ── Doctor Directory ───────────────────────────────────────────────────
    path("find-doctors/", views.doctors_directory, name="doctors_directory"),

    # ── Clinical Services & Specialties ───────────────────────────────────
    path("services/", views.services_view, name="services_view"),

    # ── Role Portals & Admin Login Gateway ─────────────────────────────────
    path("portals/", views.portals_gateway, name="portals_gateway"),
]
