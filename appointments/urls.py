from django.urls import path
from . import views

urlpatterns = [
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/book/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("appointments/<int:pk>/status/", views.appointment_status_update, name="appointment_status_update"),
]
