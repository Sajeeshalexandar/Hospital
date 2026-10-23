from django.urls import path
from . import views

urlpatterns = [
    path("hospital-admin/departments/", views.department_list, name="department_list"),
    path("hospital-admin/departments/create/", views.department_create, name="department_create"),
    path("hospital-admin/departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("hospital-admin/departments/<int:pk>/delete/", views.department_delete, name="department_delete"),
]
