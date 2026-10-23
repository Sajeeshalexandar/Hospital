from django.urls import path
from . import views

urlpatterns = [
    # Subscription Plans
    path("super-admin/plans/", views.plan_list, name="plan_list"),
    path("super-admin/plans/create/", views.plan_create, name="plan_create"),
    path("super-admin/plans/<int:pk>/edit/", views.plan_edit, name="plan_edit"),

    # Hospital Subscriptions
    path("super-admin/subscriptions/", views.subscription_list, name="subscription_list"),
    path("super-admin/subscriptions/create/", views.subscription_create, name="subscription_create"),
    path("super-admin/subscriptions/<int:pk>/edit/", views.subscription_edit, name="subscription_edit"),
]
