from django.urls import path
from . import views

urlpatterns = [
    path("hospital-admin/staff/", views.staff_list, name="staff_list"),
    path("hospital-admin/staff/create/", views.staff_create, name="staff_create"),
    path("hospital-admin/staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("hospital-admin/staff/<int:pk>/delete/", views.staff_delete, name="staff_delete"),
]
