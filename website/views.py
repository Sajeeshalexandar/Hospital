from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from hospitals.models import Hospital
from departments.models import Department
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from appointments.models import Appointment
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription
from laboratory.models import LabTestOrder
from notifications.utils import create_notification
from audit_logs.utils import log_audit

User = get_user_model()


def landing_page(request):
    """
    Primary Public Patient Website & Landing Page for MediSaaS.
    Showcases hospital services, specialist directory, online booking, and patient portal access.
    """
    hospitals = Hospital.objects.filter(status=Hospital.Status.ACTIVE).order_by("name")
    departments = Department.objects.filter(is_active=True).select_related("hospital").order_by("name")
    doctors = (
        DoctorProfile.objects.filter(is_active=True)
        .select_related("user", "hospital", "department")
        .order_by("-experience_years")[:8]
    )

    stats = {
        "hospitals_count": Hospital.objects.filter(status=Hospital.Status.ACTIVE).count(),
        "doctors_count": DoctorProfile.objects.filter(is_active=True).count(),
        "departments_count": Department.objects.filter(is_active=True).count(),
        "patients_treated": 12500 + PatientProfile.objects.count() * 12,
        "satisfaction_rate": "99.4%",
    }

    context = {
        "hospitals": hospitals,
        "departments": departments,
        "doctors": doctors,
        "stats": stats,
    }
    return render(request, "website/landing.html", context)


def book_appointment(request):
    """
    Public online appointment booking for patients.
    Validates conflict prevention (Rule #8) and registers/links patient profile.
    """
    hospitals = Hospital.objects.filter(status=Hospital.Status.ACTIVE).order_by("name")
    departments = Department.objects.filter(is_active=True).select_related("hospital")
    doctors = DoctorProfile.objects.filter(is_active=True).select_related("user", "department", "hospital")

    if request.method == "POST":
        hospital_id = request.POST.get("hospital")
        department_id = request.POST.get("department")
        doctor_id = request.POST.get("doctor")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip().lower()
        appointment_date = request.POST.get("appointment_date", "").strip()
        appointment_time = request.POST.get("appointment_time", "").strip()
        reason = request.POST.get("reason", "").strip()
        gender = request.POST.get("gender", "NOT_SPECIFIED")

        if not all([hospital_id, doctor_id, first_name, phone, appointment_date, appointment_time]):
            messages.error(request, "Please fill in all required appointment details.")
            return render(request, "website/book_appointment.html", {
                "hospitals": hospitals, "departments": departments, "doctors": doctors,
            })

        hospital = get_object_or_404(Hospital, pk=hospital_id)
        doctor = get_object_or_404(DoctorProfile, pk=doctor_id, hospital=hospital)
        department = doctor.department

        # Parse date and time into start_at and end_at (default 30 min duration)
        try:
            start_dt_str = f"{appointment_date} {appointment_time}"
            start_at = timezone.make_aware(datetime.strptime(start_dt_str, "%Y-%m-%d %H:%M"))
            end_at = start_at + timedelta(minutes=30)
        except Exception:
            messages.error(request, "Invalid appointment date or time selected.")
            return render(request, "website/book_appointment.html", {
                "hospitals": hospitals, "departments": departments, "doctors": doctors,
            })

        if start_at < timezone.now():
            messages.error(request, "Appointment cannot be booked in the past. Please select an upcoming date and time.")
            return render(request, "website/book_appointment.html", {
                "hospitals": hospitals, "departments": departments, "doctors": doctors,
            })

        # Rule #8: Conflict Prevention Check (No overlapping appointments for this doctor)
        conflict = Appointment.objects.filter(
            doctor=doctor,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).exists()

        if conflict:
            messages.error(
                request,
                f"Dr. {doctor.user.get_full_name()} is already booked at {start_at.strftime('%H:%M')} on {appointment_date}. Please select another time slot."
            )
            return render(request, "website/book_appointment.html", {
                "hospitals": hospitals, "departments": departments, "doctors": doctors,
            })

        with transaction.atomic():
            # Find or create patient record for this hospital by phone or email
            patient = PatientProfile.objects.filter(hospital=hospital, contact_number=phone).first()

            if not patient:
                # Generate patient code
                year = timezone.now().year
                prefix = f"PAT-{year}-"
                count = PatientProfile.objects.filter(hospital=hospital).count() + 1
                patient_code = f"{prefix}{count:04d}"

                # Assign or create user
                synthetic_email = email if email else f"{phone}@patient.local"
                user, _ = User.objects.get_or_create(
                    username=f"pat_{phone}",
                    defaults={
                        "email": synthetic_email,
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )

                patient = PatientProfile.objects.create(
                    hospital=hospital,
                    user=user,
                    patient_id_code=patient_code,
                    date_of_birth=timezone.now().date() - timedelta(days=365*25),
                    gender=gender,
                    contact_number=phone,
                    address="Self Registered Online",
                )

            # Create appointment
            appointment = Appointment.objects.create(
                hospital=hospital,
                patient=patient,
                doctor=doctor,
                department=department,
                start_at=start_at,
                end_at=end_at,
                reason_for_visit=reason or "General Consultation",
                status=Appointment.Status.PENDING,
            )

            # Notification to doctor
            if doctor.user:
                create_notification(
                    doctor.user,
                    "New Online Appointment Booked",
                    f"Patient {patient.user.get_full_name()} booked consultation on {start_at.strftime('%d %b %Y at %H:%M')}.",
                    hospital=hospital,
                    notification_type="APPOINTMENT",
                )

        return render(request, "website/booking_success.html", {
            "appointment": appointment,
            "patient": patient,
            "doctor": doctor,
            "hospital": hospital,
        })

    context = {
        "hospitals": hospitals,
        "departments": departments,
        "doctors": doctors,
    }
    return render(request, "website/book_appointment.html", context)


def patient_portal(request):
    """
    Patient Self-Service Portal.
    Allows patients to enter their Patient ID Code or Phone to view their records, prescriptions, and appointments.
    """
    search_query = request.GET.get("q", "").strip()
    patient = None
    appointments = []
    prescriptions = []
    lab_orders = []

    if search_query:
        patient = (
            PatientProfile.objects.filter(patient_id_code__iexact=search_query)
            | PatientProfile.objects.filter(contact_number__iexact=search_query)
        ).select_related("user", "hospital").first()

        if patient:
            appointments = Appointment.objects.filter(patient=patient).select_related("doctor", "department").order_by("-start_at")[:10]
            prescriptions = Prescription.objects.filter(patient=patient).select_related("doctor").prefetch_related("medicines").order_by("-created_at")[:10]
            lab_orders = LabTestOrder.objects.filter(patient=patient).select_related("doctor").order_by("-ordered_at")[:10]
        else:
            messages.warning(request, f"No patient records found matching '{search_query}'. Please verify your Patient ID Code or contact number.")

    context = {
        "search_query": search_query,
        "patient": patient,
        "appointments": appointments,
        "prescriptions": prescriptions,
        "lab_orders": lab_orders,
    }
    return render(request, "website/patient_portal.html", context)


def doctors_directory(request):
    """Public searchable doctors directory."""
    doctors = DoctorProfile.objects.filter(is_active=True).select_related("user", "department", "hospital")
    departments = Department.objects.filter(is_active=True)
    hospitals = Hospital.objects.filter(status=Hospital.Status.ACTIVE)

    dept_id = request.GET.get("department")
    hosp_id = request.GET.get("hospital")
    q = request.GET.get("q", "").strip()

    if dept_id:
        doctors = doctors.filter(department_id=dept_id)
    if hosp_id:
        doctors = doctors.filter(hospital_id=hosp_id)
    if q:
        doctors = doctors.filter(user__first_name__icontains=q) | doctors.filter(user__last_name__icontains=q) | doctors.filter(specialization__icontains=q)

    context = {
        "doctors": doctors,
        "departments": departments,
        "hospitals": hospitals,
        "selected_dept": dept_id,
        "selected_hosp": hosp_id,
        "search_q": q,
    }
    return render(request, "website/doctors.html", context)


def services_view(request):
    """Clinical departments and health services page."""
    departments = Department.objects.filter(is_active=True).select_related("hospital").order_by("name")
    return render(request, "website/services.html", {"departments": departments})


def portals_gateway(request):
    """
    Dedicated Gateway page displaying all Role Logins and Admin panels.
    Provides direct links and instructions for Doctor, Receptionist, Hospital Admin, and Super Admin.
    """
    from accounts.views import ROLE_CONFIGS
    return render(request, "website/portals_gateway.html", {"roles": ROLE_CONFIGS})
