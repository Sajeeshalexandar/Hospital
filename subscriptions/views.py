from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import superadmin_required
from .models import SubscriptionPlan, HospitalSubscription
from .forms import SubscriptionPlanForm, HospitalSubscriptionForm


# ══════════════════════════════════════════════════════════════════════════════
# SUPER ADMIN — Subscription Plans
# ══════════════════════════════════════════════════════════════════════════════

@superadmin_required
def plan_list(request):
    """Super Admin: list all SaaS subscription plans."""
    plans = SubscriptionPlan.objects.all().order_by("-created_at")
    context = {"plans": plans}
    return render(request, "super_admin/subscriptions/plan_list.html", context)


@superadmin_required
def plan_create(request):
    """Super Admin: create a new subscription plan."""
    form = SubscriptionPlanForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            plan = form.save()
            messages.success(request, f"Subscription Plan '{plan.name}' created.")
            return redirect("plan_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "action": "Create"}
    return render(request, "super_admin/subscriptions/plan_form.html", context)


@superadmin_required
def plan_edit(request, pk):
    """Super Admin: edit an existing subscription plan."""
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    form = SubscriptionPlanForm(request.POST or None, instance=plan)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Subscription Plan '{plan.name}' updated.")
            return redirect("plan_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "action": "Edit", "plan": plan}
    return render(request, "super_admin/subscriptions/plan_form.html", context)


# ══════════════════════════════════════════════════════════════════════════════
# SUPER ADMIN — Hospital Subscriptions
# ══════════════════════════════════════════════════════════════════════════════

@superadmin_required
def subscription_list(request):
    """Super Admin: list all hospital active/inactive subscriptions."""
    subscriptions = HospitalSubscription.objects.select_related("hospital", "plan").all().order_by("-created_at")
    context = {"subscriptions": subscriptions}
    return render(request, "super_admin/subscriptions/subscription_list.html", context)


@superadmin_required
def subscription_create(request):
    """Super Admin: assign a subscription plan to a hospital."""
    form = HospitalSubscriptionForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            sub = form.save()
            messages.success(request, f"Subscription assigned to '{sub.hospital.name}'.")
            return redirect("subscription_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "action": "Create"}
    return render(request, "super_admin/subscriptions/subscription_form.html", context)


@superadmin_required
def subscription_edit(request, pk):
    """Super Admin: modify an existing hospital subscription."""
    sub = get_object_or_404(HospitalSubscription, pk=pk)
    form = HospitalSubscriptionForm(request.POST or None, instance=sub)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Subscription for '{sub.hospital.name}' updated.")
            return redirect("subscription_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "action": "Edit", "sub": sub}
    return render(request, "super_admin/subscriptions/subscription_form.html", context)
