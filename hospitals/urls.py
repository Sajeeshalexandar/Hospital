from django.urls import path
from . import views

urlpatterns = [
    # Super Admin - Hospital CRUD
    path("super-admin/hospitals/", views.hospital_list, name="hospital_list"),
    path("super-admin/hospitals/create/", views.hospital_create, name="hospital_create"),
    path("super-admin/hospitals/<int:pk>/", views.hospital_detail, name="hospital_detail"),
    path("super-admin/hospitals/<int:pk>/edit/", views.hospital_edit, name="hospital_edit"),
    path("super-admin/hospitals/<int:pk>/delete/", views.hospital_delete, name="hospital_delete"),

    # Hospital Admin - My Hospital & Settings
    path("hospital-admin/my-hospital/", views.my_hospital_profile, name="my_hospital_profile"),
    path("hospital-admin/my-hospital/settings/", views.my_hospital_settings, name="my_hospital_settings"),
]
