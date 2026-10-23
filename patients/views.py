from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.decorators import roles_required, hospital_admin_required
from accounts.helpers import get_user_hospital, get_user_role
from audit_logs.utils import log_audit
from .models import PatientProfile
from .forms import PatientForm

User = get_user_model()


def _generate_patient_code(hospital):
    """Auto-generate an incremental patient code for a hospital: PAT-YYYY-0001."""
    year = timezone.now().year
    prefix = f"PAT-{year}-"
    last_patient = (
        PatientProfile.objects.filter(hospital=hospital, patient_id_code__startswith=prefix)
        .order_by("-id")
        .first()
    )
    if last_patient and last_patient.patient_id_code:
        try:
            last_num = int(last_patient.patient_id_code.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = PatientProfile.objects.filter(hospital=hospital).count() + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR")
def patient_list(request):
    """List all registered patients in the hospital with search and filter options."""
    hospital = get_user_hospital(request.user)
    patients = (
        PatientProfile.objects.select_related("user", "hospital")
        .filter(hospital=hospital)
        .order_by("-created_at")
    )

    q = request.GET.get("q", "").strip()
    blood_group = request.GET.get("blood_group", "")
    gender = request.GET.get("gender", "")

    if q:
        patients = (
            patients.filter(patient_id_code__icontains=q)
            | patients.filter(user__first_name__icontains=q)
            | patients.filter(user__last_name__icontains=q)
            | patients.filter(contact_number__icontains=q)
        )

    if blood_group:
        patients = patients.filter(blood_group=blood_group)

    if gender:
        patients = patients.filter(gender=gender)

    user_role = get_user_role(request.user)

    context = {
        "hospital": hospital,
        "patients": patients,
        "q": q,
        "blood_group": blood_group,
        "gender": gender,
        "blood_choices": PatientProfile.BloodGroup.choices,
        "gender_choices": PatientProfile.Gender.choices,
        "can_edit": user_role in ["HOSPITAL_ADMIN", "RECEPTIONIST"] or request.user.is_superuser,
        "user_role": user_role,
    }
    return render(request, "patients/list.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST")
def patient_create(request):
    """Register a new patient into the hospital system."""
    hospital = get_user_hospital(request.user)
    form = PatientForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                first_name = form.cleaned_data["first_name"]
                last_name = form.cleaned_data["last_name"]
                email = form.cleaned_data.get("email")

                code = form.cleaned_data.get("patient_id_code")
                if not code:
                    code = _generate_patient_code(hospital)

                # Generate or assign User record for patient full name
                if email:
                    user, _ = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": email,
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )
                else:
                    synthetic_email = f"{code.lower()}@patient.local"
                    user, _ = User.objects.get_or_create(
                        username=code.lower(),
                        defaults={
                            "email": synthetic_email,
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )

                patient = form.save(commit=False)
                patient.hospital = hospital
                patient.patient_id_code = code
                patient.user = user
                patient.save()

                log_audit(
                    request,
                    "REGISTER_PATIENT",
                    "PatientProfile",
                    patient.pk,
                    f"Registered patient {patient.patient_id_code} ({user.get_full_name()})",
                    hospital=hospital,
                )

            messages.success(request, f"Patient '{user.get_full_name()}' registered with ID: {code}.")
            return redirect("patient_detail", pk=patient.pk)
        else:
            messages.error(request, "Please fix the errors in the form.")

    context = {"form": form, "hospital": hospital, "action": "Register"}
    return render(request, "patients/form.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR")
def patient_detail(request, pk):
    """View patient details, demographics, and emergency contact."""
    hospital = get_user_hospital(request.user)
    patient = get_object_or_404(
        PatientProfile.objects.select_related("user", "hospital"),
        pk=pk,
        hospital=hospital,
    )
    user_role = get_user_role(request.user)

    context = {
        "patient": patient,
        "hospital": hospital,
        "can_edit": user_role in ["HOSPITAL_ADMIN", "RECEPTIONIST"] or request.user.is_superuser,
        "user_role": user_role,
    }
    return render(request, "patients/detail.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST")
def patient_edit(request, pk):
    """Edit patient details and contact info."""
    hospital = get_user_hospital(request.user)
    patient = get_object_or_404(PatientProfile, pk=pk, hospital=hospital)
    form = PatientForm(request.POST or None, instance=patient)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                if patient.user:
                    patient.user.first_name = form.cleaned_data["first_name"]
                    patient.user.last_name = form.cleaned_data["last_name"]
                    new_email = form.cleaned_data.get("email")
                    if new_email and not User.objects.filter(email=new_email).exclude(pk=patient.user.pk).exists():
                        patient.user.email = new_email
                    patient.user.save()
                form.save()

            messages.success(request, f"Details for patient '{patient.patient_id_code}' updated.")
            return redirect("patient_detail", pk=patient.pk)
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "patient": patient, "hospital": hospital, "action": "Edit"}
    return render(request, "patients/form.html", context)


@hospital_admin_required
def patient_delete(request, pk):
    """Deactivate or remove a patient (Hospital Admin only)."""
    hospital = get_user_hospital(request.user)
    patient = get_object_or_404(PatientProfile, pk=pk, hospital=hospital)

    if request.method == "POST":
        code = patient.patient_id_code
        patient.is_active = False
        patient.save()
        messages.success(request, f"Patient '{code}' has been deactivated.")
        return redirect("patient_list")

    context = {"patient": patient, "hospital": hospital}
    return render(request, "patients/confirm_delete.html", context)
