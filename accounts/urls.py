from django.urls import path
from . import views

urlpatterns = [
    # Keep the legacy login URL out of the role-login flow.
    path("login/", views.login_redirect, name="login"),

    # Dedicated role-specific login URLs
    path("login/super-admin/", views.super_admin_login_view, name="super_admin_login"),
    path("login/hospital-admin/", views.hospital_admin_login_view, name="hospital_admin_login"),
    path("login/doctor/", views.doctor_login_view, name="doctor_login"),
    path("login/receptionist/", views.receptionist_login_view, name="receptionist_login"),
    path("login/staff/", views.staff_login_view, name="staff_login"),
    path("login/patient/", views.patient_login_view, name="patient_login"),

    # Logout
    path("logout/", views.logout_view, name="logout"),
]
