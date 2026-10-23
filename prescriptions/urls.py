from django.urls import path
from . import views

urlpatterns = [
    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path("prescriptions/create/<int:appointment_id>/", views.prescription_create, name="prescription_create"),
    path("prescriptions/<int:pk>/", views.prescription_detail, name="prescription_detail"),
    path("prescriptions/<int:pk>/add-medicine/", views.prescription_medicine_add, name="prescription_medicine_add"),
    path("prescriptions/medicine/<int:pk>/delete/", views.prescription_medicine_delete, name="prescription_medicine_delete"),
]
