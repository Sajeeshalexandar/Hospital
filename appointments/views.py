from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from accounts.decorators import roles_required
from accounts.helpers import get_user_hospital, get_user_role
from audit_logs.utils import log_audit
from notifications.utils import create_notification
from doctors.models import DoctorProfile
from .models import Appointment
from .forms import AppointmentBookingForm, AppointmentStatusForm


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR")
def appointment_list(request):
    """List appointments for the hospital with filters for date, status, and doctor."""
    hospital = get_user_hospital(request.user)
    role = get_user_role(request.user)

    appointments = Appointment.objects.select_related(
        "patient", "patient__user", "doctor", "doctor__user", "department"
    ).filter(hospital=hospital).order_by("-start_at")

    # If logged in as Doctor, can default to own appointments or filter
    doctor_profile = None
    if role == "DOCTOR":
        doctor_profile = DoctorProfile.objects.filter(user=request.user, hospital=hospital).first()

    status = request.GET.get("status", "")
    doc_id = request.GET.get("doctor", "")
    date_filter = request.GET.get("date", "")
    q = request.GET.get("q", "").strip()

    if status:
        appointments = appointments.filter(status=status)

    if doc_id:
        appointments = appointments.filter(doctor_id=doc_id)
    elif role == "DOCTOR" and doctor_profile and not request.GET.get("all"):
        # By default, a doctor sees their own appointments unless "all" is set
        appointments = appointments.filter(doctor=doctor_profile)

    if date_filter:
        appointments = appointments.filter(start_at__date=date_filter)

    if q:
        appointments = appointments.filter(
            patient__patient_id_code__icontains=q
        ) | appointments.filter(
            patient__user__first_name__icontains=q
        ) | appointments.filter(
            patient__user__last_name__icontains=q
        ) | appointments.filter(
            reason_for_visit__icontains=q
        )

    doctors = DoctorProfile.objects.filter(hospital=hospital, is_active=True).select_related("user")

    context = {
        "hospital": hospital,
        "appointments": appointments,
        "doctors": doctors,
        "status_choices": Appointment.Status.choices,
        "status_filter": status,
        "doc_id": doc_id,
        "date_filter": date_filter,
        "q": q,
        "user_role": role,
        "doctor_profile": doctor_profile,
    }
    return render(request, "appointments/list.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR")
def appointment_create(request):
    """Schedule / book a new patient consultation appointment."""
    hospital = get_user_hospital(request.user)
    form = AppointmentBookingForm(request.POST or None, hospital=hospital)

    if request.method == "POST":
        if form.is_valid():
            appt = form.save(commit=False)
            appt.hospital = hospital
            appt.created_by = request.user
            appt.status = Appointment.Status.PENDING
            appt.save()

            log_audit(
                request,
                "SCHEDULE_APPOINTMENT",
                "Appointment",
                appt.pk,
                f"Scheduled appointment for {appt.patient.patient_id_code} with Dr. {appt.doctor.user.get_full_name()}",
                hospital=hospital,
            )

            if appt.doctor and appt.doctor.user:
                create_notification(
                    appt.doctor.user,
                    "New Appointment Scheduled",
                    f"Consultation scheduled with {appt.patient.user.get_full_name() if appt.patient.user else 'patient'} on {appt.start_at.strftime('%d %b at %H:%M')}.",
                    hospital=hospital,
                    notification_type="APPOINTMENT",
                )

            messages.success(
                request,
                f"Appointment scheduled for {appt.patient.patient_id_code} with Dr. {appt.doctor.user.get_full_name()} on {appt.start_at.strftime('%d %b %Y at %H:%M')}."
            )
            return redirect("appointment_detail", pk=appt.pk)
        else:
            messages.error(request, "Could not book appointment. Please review the errors below.")

    context = {"form": form, "hospital": hospital}
    return render(request, "appointments/book.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR")
def appointment_detail(request, pk):
    """Appointment clinical workspace: view details, update status, view/add records and prescriptions."""
    hospital = get_user_hospital(request.user)
    appt = get_object_or_404(
        Appointment.objects.select_related(
            "patient", "patient__user", "doctor", "doctor__user", "department", "hospital"
        ),
        pk=pk,
        hospital=hospital,
    )
    status_form = AppointmentStatusForm(instance=appt)
    role = get_user_role(request.user)

    medical_records = appt.medical_records.all().order_by("-created_at")
    prescriptions = appt.prescriptions.prefetch_related("medicines").all().order_by("-created_at")

    context = {
        "appt": appt,
        "status_form": status_form,
        "medical_records": medical_records,
        "prescriptions": prescriptions,
        "hospital": hospital,
        "user_role": role,
    }
    return render(request, "appointments/detail.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR")
def appointment_status_update(request, pk):
    """Update appointment status (CONFIRMED, COMPLETED, CANCELLED)."""
    hospital = get_user_hospital(request.user)
    appt = get_object_or_404(Appointment, pk=pk, hospital=hospital)

    if request.method == "POST":
        form = AppointmentStatusForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()

            log_audit(
                request,
                f"APPOINTMENT_{appt.status}",
                "Appointment",
                appt.pk,
                f"Appointment #{appt.pk} status updated to {appt.get_status_display()}",
                hospital=hospital,
            )

            messages.success(request, f"Appointment status updated to '{appt.get_status_display()}'.")
        else:
            messages.error(request, "Failed to update status. Please provide a reason if cancelling.")

    return redirect("appointment_detail", pk=appt.pk)
