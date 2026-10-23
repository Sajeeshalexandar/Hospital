from django.urls import path
from . import views

urlpatterns = [
    path("medical-records/", views.record_list, name="record_list"),
    path("medical-records/create/<int:appointment_id>/", views.record_create, name="record_create"),
    path("medical-records/<int:pk>/", views.record_detail, name="record_detail"),
    path("medical-records/<int:pk>/edit/", views.record_edit, name="record_edit"),
]
