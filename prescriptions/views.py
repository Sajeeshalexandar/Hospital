from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from accounts.decorators import roles_required
from accounts.helpers import get_user_hospital, get_user_role
from audit_logs.utils import log_audit
from notifications.utils import create_notification
from appointments.models import Appointment
from .models import Prescription, PrescriptionMedicine
from .forms import PrescriptionForm, PrescriptionMedicineForm


def _generate_prescription_number(hospital):
    """Auto-generate incremental prescription number: RX-YYYY-0001."""
    year = timezone.now().year
    prefix = f"RX-{year}-"
    last_rx = (
        Prescription.objects.filter(hospital=hospital, prescription_number__startswith=prefix)
        .order_by("-id")
        .first()
    )
    if last_rx and last_rx.prescription_number:
        try:
            last_num = int(last_rx.prescription_number.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = Prescription.objects.filter(hospital=hospital).count() + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST")
def prescription_list(request):
    """List prescriptions in the hospital."""
    hospital = get_user_hospital(request.user)
    prescriptions = Prescription.objects.select_related(
        "patient", "patient__user", "doctor", "doctor__user", "appointment"
    ).filter(hospital=hospital).order_by("-created_at")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    if q:
        prescriptions = prescriptions.filter(
            prescription_number__icontains=q
        ) | prescriptions.filter(
            patient__patient_id_code__icontains=q
        ) | prescriptions.filter(
            patient__user__first_name__icontains=q
        )

    if status:
        prescriptions = prescriptions.filter(status=status)

    context = {
        "hospital": hospital,
        "prescriptions": prescriptions,
        "status_choices": Prescription.Status.choices,
        "status_filter": status,
        "q": q,
    }
    return render(request, "prescriptions/list.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR")
def prescription_create(request, appointment_id):
    """Create a new prescription record for an appointment."""
    hospital = get_user_hospital(request.user)
    appt = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor", "hospital"),
        pk=appointment_id,
        hospital=hospital,
    )
    form = PrescriptionForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            rx = form.save(commit=False)
            rx.hospital = hospital
            rx.appointment = appt
            rx.patient = appt.patient
            rx.doctor = appt.doctor

            if not rx.prescription_number:
                rx.prescription_number = _generate_prescription_number(hospital)

            rx.status = Prescription.Status.DRAFT
            rx.save()

            messages.success(request, f"Prescription {rx.prescription_number} initiated. Add medicines below.")
            return redirect("prescription_detail", pk=rx.pk)
        else:
            messages.error(request, "Please check the form for errors.")

    context = {
        "form": form,
        "appt": appt,
        "hospital": hospital,
    }
    return render(request, "prescriptions/form.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST")
def prescription_detail(request, pk):
    """Prescription clinical sheet: manage medicine line items and status."""
    hospital = get_user_hospital(request.user)
    rx = get_object_or_404(
        Prescription.objects.select_related(
            "patient", "patient__user", "doctor", "doctor__user", "appointment", "hospital"
        ).prefetch_related("medicines"),
        pk=pk,
        hospital=hospital,
    )
    med_form = PrescriptionMedicineForm()
    role = get_user_role(request.user)

    # Issue or Cancel Prescription
    if request.method == "POST" and "update_status" in request.POST:
        if role not in ["HOSPITAL_ADMIN", "DOCTOR"] and not request.user.is_superuser:
            messages.error(request, "Only doctors can sign and issue prescriptions.")
            return redirect("prescription_detail", pk=pk)

        new_status = request.POST.get("update_status")
        if new_status in Prescription.Status.values:
            rx.status = new_status
            if new_status == Prescription.Status.ISSUED:
                rx.issued_at = timezone.now()
            rx.save()

            log_audit(
                request,
                f"PRESCRIPTION_{rx.status}",
                "Prescription",
                rx.pk,
                f"Prescription {rx.prescription_number} status changed to {rx.get_status_display()}",
                hospital=hospital,
            )

            if new_status == Prescription.Status.ISSUED and rx.patient.user:
                create_notification(
                    rx.patient.user,
                    "Prescription Issued",
                    f"Dr. {rx.doctor.user.get_full_name() if rx.doctor.user else 'Doctor'} has issued prescription {rx.prescription_number}.",
                    hospital=hospital,
                    notification_type="PRESCRIPTION",
                )

            messages.success(request, f"Prescription status updated to '{rx.get_status_display()}'.")
            return redirect("prescription_detail", pk=pk)

    context = {
        "rx": rx,
        "med_form": med_form,
        "medicines": rx.medicines.all(),
        "hospital": hospital,
        "can_edit": (role in ["HOSPITAL_ADMIN", "DOCTOR"] or request.user.is_superuser) and rx.status == Prescription.Status.DRAFT,
        "user_role": role,
    }
    return render(request, "prescriptions/detail.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR")
def prescription_medicine_add(request, pk):
    """Add a medicine line item to a prescription."""
    hospital = get_user_hospital(request.user)
    rx = get_object_or_404(Prescription, pk=pk, hospital=hospital)

    if rx.status != Prescription.Status.DRAFT:
        messages.error(request, "Cannot modify medicines on an already issued or cancelled prescription.")
        return redirect("prescription_detail", pk=pk)

    if request.method == "POST":
        form = PrescriptionMedicineForm(request.POST)
        if form.is_valid():
            med = form.save(commit=False)
            med.prescription = rx
            med.save()
            messages.success(request, f"Added '{med.medicine_name}' to prescription.")
        else:
            messages.error(request, "Could not add medicine. Please review fields.")

    return redirect("prescription_detail", pk=pk)


@roles_required("HOSPITAL_ADMIN", "DOCTOR")
def prescription_medicine_delete(request, pk):
    """Remove a medicine line item."""
    hospital = get_user_hospital(request.user)
    med = get_object_or_404(PrescriptionMedicine, pk=pk, prescription__hospital=hospital)
    rx_pk = med.prescription.pk

    if med.prescription.status != Prescription.Status.DRAFT:
        messages.error(request, "Cannot modify medicines on an already issued prescription.")
        return redirect("prescription_detail", pk=rx_pk)

    if request.method == "POST":
        med.delete()
        messages.success(request, "Medicine item removed.")

    return redirect("prescription_detail", pk=rx_pk)
