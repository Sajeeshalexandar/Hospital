from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import superadmin_required, hospital_admin_required
from accounts.helpers import get_user_hospital
from .models import Hospital, HospitalSettings
from .forms import HospitalForm, HospitalSettingsForm


# ══════════════════════════════════════════════════════════════════════════════
# SUPER ADMIN — Hospital CRUD
# ══════════════════════════════════════════════════════════════════════════════

@superadmin_required
def hospital_list(request):
    """Super Admin: list every hospital with search and status filter."""
    hospitals = Hospital.objects.all().order_by("-created_at")

    # Simple search by name or city
    q = request.GET.get("q", "").strip()
    if q:
        hospitals = hospitals.filter(name__icontains=q) | hospitals.filter(city__icontains=q)

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        hospitals = hospitals.filter(status=status)

    context = {
        "hospitals": hospitals,
        "q": q,
        "status_filter": status,
        "status_choices": Hospital.Status.choices,
        "total": Hospital.objects.count(),
    }
    return render(request, "super_admin/hospitals/list.html", context)


@superadmin_required
def hospital_create(request):
    """Super Admin: create a new hospital and auto-create its settings."""
    form = HospitalForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            hospital = form.save()
            # Always auto-create a HospitalSettings row so Hospital Admins
            # can edit settings without a DoesNotExist crash.
            HospitalSettings.objects.get_or_create(hospital=hospital)
            messages.success(
                request,
                f"Hospital '{hospital.name}' created successfully.",
            )
            return redirect("hospital_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "action": "Create"}
    return render(request, "super_admin/hospitals/form.html", context)


@superadmin_required
def hospital_detail(request, pk):
    """Super Admin: read-only overview of a single hospital."""
    hospital = get_object_or_404(Hospital, pk=pk)
    settings_obj = getattr(hospital, "settings", None)
    subscriptions = hospital.subscriptions.select_related("plan").order_by("-start_date")
    memberships   = hospital.memberships.select_related("user").order_by("role")

    context = {
        "hospital": hospital,
        "settings_obj": settings_obj,
        "subscriptions": subscriptions,
        "memberships": memberships,
    }
    return render(request, "super_admin/hospitals/detail.html", context)


@superadmin_required
def hospital_edit(request, pk):
    """Super Admin: edit an existing hospital."""
    hospital = get_object_or_404(Hospital, pk=pk)
    form = HospitalForm(request.POST or None, instance=hospital)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Hospital '{hospital.name}' updated.")
            return redirect("hospital_detail", pk=pk)
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "action": "Edit", "hospital": hospital}
    return render(request, "super_admin/hospitals/form.html", context)


@superadmin_required
def hospital_delete(request, pk):
    """
    Super Admin: delete a hospital.
    Only accepts POST requests (form with CSRF token).
    GET requests show a confirmation page.
    """
    hospital = get_object_or_404(Hospital, pk=pk)

    if request.method == "POST":
        name = hospital.name
        hospital.delete()
        messages.success(request, f"Hospital '{name}' has been deleted.")
        return redirect("hospital_list")

    # GET: show confirmation
    context = {"hospital": hospital}
    return render(request, "super_admin/hospitals/confirm_delete.html", context)


# ══════════════════════════════════════════════════════════════════════════════
# HOSPITAL ADMIN — View & Edit their own hospital
# ══════════════════════════════════════════════════════════════════════════════

@hospital_admin_required
def my_hospital_profile(request):
    """
    Hospital Admin: view their own hospital's profile.
    Hospital is read from the DB — never from a URL or form field.
    """
    hospital = get_user_hospital(request.user)
    if not hospital:
        messages.error(request, "No hospital associated with your account.")
        return redirect("login")

    settings_obj = getattr(hospital, "settings", None)
    departments  = hospital.departments.filter(is_active=True).order_by("name")

    context = {
        "hospital": hospital,
        "settings_obj": settings_obj,
        "departments": departments,
    }
    return render(request, "hospital_admin/my_hospital.html", context)


@hospital_admin_required
def my_hospital_settings(request):
    """
    Hospital Admin: edit their hospital's operational settings.
    They can ONLY edit settings — not the core Hospital record.
    """
    hospital = get_user_hospital(request.user)
    if not hospital:
        messages.error(request, "No hospital associated with your account.")
        return redirect("login")

    # get_or_create protects against missing settings row
    settings_obj, _ = HospitalSettings.objects.get_or_create(hospital=hospital)
    form = HospitalSettingsForm(request.POST or None, instance=settings_obj)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Hospital settings updated successfully.")
            return redirect("my_hospital_profile")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "hospital": hospital}
    return render(request, "hospital_admin/my_hospital_settings.html", context)
