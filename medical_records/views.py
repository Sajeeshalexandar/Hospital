from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import roles_required
from accounts.helpers import get_user_hospital, get_user_role
from audit_logs.utils import log_audit
from appointments.models import Appointment
from .models import MedicalRecord
from .forms import MedicalRecordForm


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST")
def record_list(request):
    """List clinical medical records within the hospital."""
    hospital = get_user_hospital(request.user)
    records = MedicalRecord.objects.select_related(
        "patient", "patient__user", "doctor", "doctor__user", "appointment"
    ).filter(hospital=hospital).order_by("-created_at")

    q = request.GET.get("q", "").strip()
    if q:
        records = records.filter(
            patient__patient_id_code__icontains=q
        ) | records.filter(
            patient__user__first_name__icontains=q
        ) | records.filter(
            diagnosis__icontains=q
        )

    context = {
        "hospital": hospital,
        "records": records,
        "q": q,
    }
    return render(request, "medical_records/list.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR")
def record_create(request, appointment_id):
    """Add a clinical diagnosis and medical record to an appointment."""
    hospital = get_user_hospital(request.user)
    appt = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor", "hospital"),
        pk=appointment_id,
        hospital=hospital,
    )
    form = MedicalRecordForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            record = form.save(commit=False)
            record.hospital = hospital
            record.appointment = appt
            record.patient = appt.patient
            record.doctor = appt.doctor
            record.created_by = request.user
            record.save()

            log_audit(
                request,
                "RECORD_DIAGNOSIS",
                "MedicalRecord",
                record.pk,
                f"Recorded diagnosis '{record.diagnosis}' for patient {record.patient.patient_id_code}",
                hospital=hospital,
            )

            # Mark appointment as completed
            if appt.status != Appointment.Status.COMPLETED:
                appt.status = Appointment.Status.COMPLETED
                appt.save()

            messages.success(request, f"Medical record created for {appt.patient.patient_id_code}.")
            return redirect("record_detail", pk=record.pk)
        else:
            messages.error(request, "Please check the form for errors.")

    context = {
        "form": form,
        "appt": appt,
        "hospital": hospital,
        "action": "Record Consultation Notes",
    }
    return render(request, "medical_records/form.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST")
def record_detail(request, pk):
    """View full clinical record, patient history, and appointment metadata."""
    hospital = get_user_hospital(request.user)
    record = get_object_or_404(
        MedicalRecord.objects.select_related(
            "patient", "patient__user", "doctor", "doctor__user", "appointment", "created_by"
        ),
        pk=pk,
        hospital=hospital,
    )
    user_role = get_user_role(request.user)

    context = {
        "record": record,
        "hospital": hospital,
        "can_edit": user_role in ["HOSPITAL_ADMIN", "DOCTOR"] or request.user.is_superuser,
    }
    return render(request, "medical_records/detail.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR")
def record_edit(request, pk):
    """Edit symptoms, diagnosis, and treatment recommendations."""
    hospital = get_user_hospital(request.user)
    record = get_object_or_404(MedicalRecord, pk=pk, hospital=hospital)
    form = MedicalRecordForm(request.POST or None, instance=record)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Medical record updated successfully.")
            return redirect("record_detail", pk=record.pk)
        else:
            messages.error(request, "Please fix the errors below.")

    context = {
        "form": form,
        "record": record,
        "appt": record.appointment,
        "hospital": hospital,
        "action": "Update Clinical Record",
    }
    return render(request, "medical_records/form.html", context)
