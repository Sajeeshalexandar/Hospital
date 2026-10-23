from django.urls import path
from . import views

urlpatterns = [
    path("billing/invoices/", views.invoice_list, name="invoice_list"),
    path("billing/invoices/create/", views.invoice_create, name="invoice_create"),
    path("billing/invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("billing/invoices/<int:pk>/items/add/", views.invoice_item_add, name="invoice_item_add"),
    path("billing/invoices/<int:invoice_pk>/items/<int:pk>/delete/", views.invoice_item_delete, name="invoice_item_delete"),
    path("billing/invoices/<int:pk>/payments/record/", views.payment_record, name="payment_record"),
    path("billing/invoices/<int:pk>/status/", views.invoice_status_update, name="invoice_status_update"),
]
