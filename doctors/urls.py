from django.urls import path
from . import views

urlpatterns = [
    # Doctor Roster & Profile
    path("hospital-admin/doctors/", views.doctor_list, name="doctor_list"),
    path("hospital-admin/doctors/create/", views.doctor_create, name="doctor_create"),
    path("hospital-admin/doctors/<int:pk>/", views.doctor_detail, name="doctor_detail"),
    path("hospital-admin/doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("hospital-admin/doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),

    # Availability Management
    path("hospital-admin/doctors/<int:pk>/availability/add/", views.doctor_availability_add, name="doctor_availability_add"),
    path("hospital-admin/doctors/availability/<int:pk>/delete/", views.doctor_availability_delete, name="doctor_availability_delete"),

    # Doctor Self-Service
    path("doctor/my-availability/", views.my_availability, name="my_availability"),
]
