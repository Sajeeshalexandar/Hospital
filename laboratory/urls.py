from django.urls import path
from . import views

urlpatterns = [
    path("laboratory/orders/", views.order_list, name="lab_order_list"),
    path("laboratory/orders/create/", views.order_create, name="lab_order_create"),
    path("laboratory/orders/<int:pk>/status/", views.order_status_update, name="lab_order_status_update"),
    path("laboratory/orders/<int:pk>/report/", views.report_upload, name="lab_report_upload"),
    path("laboratory/reports/<int:pk>/", views.report_detail, name="lab_report_detail"),
]
