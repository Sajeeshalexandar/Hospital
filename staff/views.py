from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model

from accounts.decorators import hospital_admin_required
from accounts.helpers import get_user_hospital
from memberships.models import HospitalMembership
from .models import StaffProfile
from .forms import StaffCreateForm, StaffEditForm

User = get_user_model()


@hospital_admin_required
def staff_list(request):
    """List all staff and receptionists in the hospital."""
    hospital = get_user_hospital(request.user)
    staff_members = StaffProfile.objects.select_related("user").filter(hospital=hospital).order_by("user__first_name")

    q = request.GET.get("q", "").strip()
    if q:
        staff_members = staff_members.filter(
            user__first_name__icontains=q
        ) | staff_members.filter(
            user__last_name__icontains=q
        ) | staff_members.filter(
            job_title__icontains=q
        ) | staff_members.filter(
            employee_code__icontains=q
        )

    context = {
        "hospital": hospital,
        "staff_members": staff_members,
        "q": q,
    }
    return render(request, "staff/list.html", context)


@hospital_admin_required
def staff_create(request):
    """Register a new staff member or receptionist."""
    hospital = get_user_hospital(request.user)
    form = StaffCreateForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                email = form.cleaned_data["email"]
                first_name = form.cleaned_data["first_name"]
                last_name = form.cleaned_data["last_name"]
                password = form.cleaned_data["password"]
                role = form.cleaned_data["role"]

                # 1. Create User
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )

                # 2. Create Membership
                HospitalMembership.objects.create(
                    user=user,
                    hospital=hospital,
                    role=role,
                    is_active=True,
                )

                # 3. Create StaffProfile
                staff = form.save(commit=False)
                staff.user = user
                staff.hospital = hospital
                staff.save()

            messages.success(request, f"Staff member '{user.get_full_name()}' registered successfully.")
            return redirect("staff_list")
        else:
            messages.error(request, "Please fix the errors in the form.")

    context = {"form": form, "hospital": hospital, "action": "Register"}
    return render(request, "staff/form.html", context)


@hospital_admin_required
def staff_edit(request, pk):
    """Edit staff member details and role."""
    hospital = get_user_hospital(request.user)
    staff = get_object_or_404(StaffProfile, pk=pk, hospital=hospital)
    form = StaffEditForm(request.POST or None, instance=staff)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                staff.user.first_name = form.cleaned_data["first_name"]
                staff.user.last_name = form.cleaned_data["last_name"]
                staff.user.save()

                role = form.cleaned_data["role"]
                membership = HospitalMembership.objects.filter(
                    user=staff.user, hospital=hospital
                ).first()
                if membership:
                    membership.role = role
                    membership.save()

                form.save()

            messages.success(request, f"Staff member '{staff.user.get_full_name()}' updated.")
            return redirect("staff_list")
        else:
            messages.error(request, "Please fix the errors in the form.")

    context = {"form": form, "staff": staff, "hospital": hospital, "action": "Edit"}
    return render(request, "staff/form.html", context)


@hospital_admin_required
def staff_delete(request, pk):
    """Deactivate or remove a staff member."""
    hospital = get_user_hospital(request.user)
    staff = get_object_or_404(StaffProfile, pk=pk, hospital=hospital)

    if request.method == "POST":
        name = staff.user.get_full_name()
        staff.is_active = False
        staff.save()
        messages.success(request, f"Staff member '{name}' has been deactivated.")
        return redirect("staff_list")

    context = {"staff": staff, "hospital": hospital}
    return render(request, "staff/confirm_delete.html", context)
