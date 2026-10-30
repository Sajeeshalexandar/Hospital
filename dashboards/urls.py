from django.urls import path
from . import views

urlpatterns = [
    # Smart dispatcher — where LOGIN_REDIRECT_URL points
    path("dashboard/", views.dashboard_dispatch, name="dashboard_dispatch"),

    # Role-specific dashboards
    path("super-admin/dashboard/", views.super_admin_dashboard, name="super_admin_dashboard"),
    path("super-admin/analytics/", views.super_admin_analytics, name="super_admin_analytics"),
    path("hospital-admin/dashboard/", views.hospital_admin_dashboard, name="hospital_admin_dashboard"),
    path("hospital-admin/analytics/", views.hospital_admin_analytics, name="hospital_admin_analytics"),
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("receptionist/dashboard/", views.receptionist_dashboard, name="receptionist_dashboard"),
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("patient/dashboard/", views.patient_dashboard, name="patient_dashboard"),
]
