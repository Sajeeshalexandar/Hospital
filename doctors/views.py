from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model

from accounts.decorators import hospital_admin_required, roles_required, doctor_required
from accounts.helpers import get_user_hospital
from memberships.models import HospitalMembership
from departments.models import Department
from .models import DoctorProfile, DoctorAvailability
from .forms import DoctorCreateForm, DoctorEditForm, DoctorAvailabilityForm

User = get_user_model()


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST")
def doctor_list(request):
    """List all doctors in the current user's hospital with search & department filter."""
    hospital = get_user_hospital(request.user)
    doctors = DoctorProfile.objects.select_related("user", "department").filter(hospital=hospital).order_by("user__first_name")

    # Search & filters
    q = request.GET.get("q", "").strip()
    dept_id = request.GET.get("department", "")

    if q:
        doctors = doctors.filter(
            user__first_name__icontains=q
        ) | doctors.filter(
            user__last_name__icontains=q
        ) | doctors.filter(
            specialization__icontains=q
        ) | doctors.filter(
            employee_code__icontains=q
        )

    if dept_id:
        doctors = doctors.filter(department_id=dept_id)

    departments = Department.objects.filter(hospital=hospital, is_active=True)

    context = {
        "hospital": hospital,
        "doctors": doctors,
        "departments": departments,
        "q": q,
        "dept_id": dept_id,
    }
    return render(request, "doctors/list.html", context)


@hospital_admin_required
def doctor_create(request):
    """
    Hospital Admin: create user account, membership, and doctor profile
    in an atomic transaction.
    """
    hospital = get_user_hospital(request.user)
    form = DoctorCreateForm(request.POST or None, hospital=hospital)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                email = form.cleaned_data["email"]
                first_name = form.cleaned_data["first_name"]
                last_name = form.cleaned_data["last_name"]
                password = form.cleaned_data["password"]

                # 1. Create or get User
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )

                # 2. Create HospitalMembership
                HospitalMembership.objects.create(
                    user=user,
                    hospital=hospital,
                    role=HospitalMembership.Role.DOCTOR,
                    is_active=True,
                )

                # 3. Create DoctorProfile
                doctor = form.save(commit=False)
                doctor.user = user
                doctor.hospital = hospital
                doctor.save()

            messages.success(request, f"Dr. {user.get_full_name()} registered successfully.")
            return redirect("doctor_detail", pk=doctor.pk)
        else:
            messages.error(request, "Please fix the errors in the form.")

    context = {"form": form, "hospital": hospital, "action": "Register"}
    return render(request, "doctors/form.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST")
def doctor_detail(request, pk):
    """Detailed view of a doctor with qualifications, consultation fees, and weekly schedule."""
    hospital = get_user_hospital(request.user)
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("user", "department", "hospital"),
        pk=pk,
        hospital=hospital,
    )
    availabilities = doctor.availabilities.all().order_by("weekday", "start_time")
    avail_form = DoctorAvailabilityForm()

    context = {
        "doctor": doctor,
        "availabilities": availabilities,
        "avail_form": avail_form,
        "hospital": hospital,
    }
    return render(request, "doctors/detail.html", context)


@hospital_admin_required
def doctor_edit(request, pk):
    """Edit doctor qualifications, department, and contact info."""
    hospital = get_user_hospital(request.user)
    doctor = get_object_or_404(DoctorProfile, pk=pk, hospital=hospital)
    form = DoctorEditForm(request.POST or None, instance=doctor, hospital=hospital)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                doctor.user.first_name = form.cleaned_data["first_name"]
                doctor.user.last_name = form.cleaned_data["last_name"]
                doctor.user.save()
                form.save()
            messages.success(request, f"Profile for Dr. {doctor.user.get_full_name()} updated.")
            return redirect("doctor_detail", pk=doctor.pk)
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "doctor": doctor, "hospital": hospital, "action": "Edit"}
    return render(request, "doctors/form.html", context)


@hospital_admin_required
def doctor_delete(request, pk):
    """Deactivate or remove a doctor."""
    hospital = get_user_hospital(request.user)
    doctor = get_object_or_404(DoctorProfile, pk=pk, hospital=hospital)

    if request.method == "POST":
        name = doctor.user.get_full_name()
        doctor.is_active = False
        doctor.save()
        messages.success(request, f"Dr. {name} has been deactivated.")
        return redirect("doctor_list")

    context = {"doctor": doctor, "hospital": hospital}
    return render(request, "doctors/confirm_delete.html", context)


@hospital_admin_required
def doctor_availability_add(request, pk):
    """Add a weekly schedule slot to a doctor's availability."""
    hospital = get_user_hospital(request.user)
    doctor = get_object_or_404(DoctorProfile, pk=pk, hospital=hospital)
    form = DoctorAvailabilityForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = doctor
            slot.save()
            messages.success(request, f"Availability slot added for {slot.get_weekday_display()}.")
        else:
            messages.error(request, "Invalid time slot. Please check end time vs start time.")

    return redirect("doctor_detail", pk=doctor.pk)


@hospital_admin_required
def doctor_availability_delete(request, pk):
    """Remove a doctor's availability slot."""
    hospital = get_user_hospital(request.user)
    slot = get_object_or_404(DoctorAvailability, pk=pk, doctor__hospital=hospital)
    doctor_pk = slot.doctor.pk
    if request.method == "POST":
        slot.delete()
        messages.success(request, "Availability slot removed.")

    return redirect("doctor_detail", pk=doctor_pk)


@doctor_required
def my_availability(request):
    """Doctor self-service page to view schedule."""
    hospital = get_user_hospital(request.user)
    doctor = get_object_or_404(DoctorProfile, user=request.user, hospital=hospital)
    availabilities = doctor.availabilities.all().order_by("weekday", "start_time")

    context = {
        "doctor": doctor,
        "availabilities": availabilities,
        "hospital": hospital,
    }
    return render(request, "doctors/my_availability.html", context)
