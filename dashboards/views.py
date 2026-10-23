from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from accounts.helpers import get_user_membership, get_user_hospital
from accounts.decorators import (
    superadmin_required,
    hospital_admin_required,
    doctor_required,
    receptionist_required,
)


@login_required(login_url="login")
def dashboard_dispatch(request):
    """
    The smart dispatcher.
    Routes authenticated users strictly by database-persisted role.
    """
    user = request.user

    # Super Admins go to the Super Admin dashboard
    if user.is_superuser:
        return redirect("super_admin_dashboard")

    # For all other users, look up their hospital membership
    membership = get_user_membership(user)

    if membership is None:
        messages.error(
            request,
            "Your account has no active hospital membership. "
            "Please contact your administrator.",
        )
        from django.contrib.auth import logout
        logout(request)
        return redirect("login")

    # Route based on role stored in DB
    role_redirects = {
        "HOSPITAL_ADMIN": "hospital_admin_dashboard",
        "DOCTOR":         "doctor_dashboard",
        "RECEPTIONIST":   "receptionist_dashboard",
        "STAFF":          "staff_dashboard",
    }

    destination = role_redirects.get(membership.role)
    if destination:
        return redirect(destination)

    # Unknown role — log out and show error
    messages.error(request, "Unrecognised role. Please contact your administrator.")
    from django.contrib.auth import logout
    logout(request)
    return redirect("login")


# ──────────────────────────────────────────────────────────────────────────────
# Super Admin Dashboard
# ──────────────────────────────────────────────────────────────────────────────

@superadmin_required
def super_admin_dashboard(request):
    from hospitals.models import Hospital
    from memberships.models import HospitalMembership
    from accounts.models import User
    from audit_logs.models import AuditLog

    context = {
        "total_hospitals": Hospital.objects.count(),
        "active_hospitals": Hospital.objects.filter(status="ACTIVE").count(),
        "total_users": User.objects.count(),
        "total_memberships": HospitalMembership.objects.filter(is_active=True).count(),
        "recent_hospitals": Hospital.objects.order_by("-created_at")[:5],
        "recent_audits": AuditLog.objects.select_related("actor", "hospital").order_by("-created_at")[:5],
    }
    return render(request, "super_admin/dashboard.html", context)


# ──────────────────────────────────────────────────────────────────────────────
# Hospital Admin Dashboard
# ──────────────────────────────────────────────────────────────────────────────

@hospital_admin_required
def hospital_admin_dashboard(request):
    from departments.models import Department
    from doctors.models import DoctorProfile
    from patients.models import PatientProfile
    from appointments.models import Appointment
    from billing.models import Invoice, Payment
    from laboratory.models import LabTestOrder

    hospital = get_user_hospital(request.user)

    # Financial stats
    total_billed = Invoice.objects.filter(hospital=hospital).exclude(
        status=Invoice.Status.VOID
    ).aggregate(Sum("total_amount"))["total_amount__sum"] or Decimal("0.00")

    total_collected = Payment.objects.filter(
        invoice__hospital=hospital, status=Payment.Status.COMPLETED
    ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

    total_outstanding = max(Decimal("0.00"), total_billed - total_collected)

    context = {
        "hospital": hospital,
        "total_departments": Department.objects.filter(hospital=hospital).count(),
        "total_doctors": DoctorProfile.objects.filter(hospital=hospital, is_active=True).count(),
        "total_patients": PatientProfile.objects.filter(hospital=hospital, is_active=True).count(),
        "upcoming_appointments": Appointment.objects.filter(
            hospital=hospital,
            status__in=["PENDING", "CONFIRMED"],
        ).select_related("patient", "doctor").order_by("start_at")[:5],
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "recent_invoices": Invoice.objects.filter(hospital=hospital).select_related("patient").order_by("-issued_at")[:5],
        "recent_lab_orders": LabTestOrder.objects.filter(hospital=hospital).select_related("patient", "doctor").order_by("-ordered_at")[:5],
    }
    return render(request, "hospital_admin/dashboard.html", context)


# ──────────────────────────────────────────────────────────────────────────────
# Doctor Dashboard
# ──────────────────────────────────────────────────────────────────────────────

@doctor_required
def doctor_dashboard(request):
    from appointments.models import Appointment
    from doctors.models import DoctorProfile
    from laboratory.models import LabTestOrder
    from prescriptions.models import Prescription

    hospital = get_user_hospital(request.user)

    # Get this doctor's profile
    try:
        doctor_profile = DoctorProfile.objects.get(user=request.user, hospital=hospital)
    except DoctorProfile.DoesNotExist:
        doctor_profile = None

    upcoming_appointments = []
    recent_prescriptions = []
    pending_labs_count = 0
    total_consultations = 0

    if doctor_profile:
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor_profile,
            status__in=["PENDING", "CONFIRMED"],
        ).select_related("patient").order_by("start_at")[:10]

        total_consultations = Appointment.objects.filter(
            doctor=doctor_profile,
            status="COMPLETED",
        ).count()

        pending_labs_count = LabTestOrder.objects.filter(
            doctor=doctor_profile,
            status__in=["REQUESTED", "COLLECTED", "PROCESSING"],
        ).count()

        recent_prescriptions = Prescription.objects.filter(
            doctor=doctor_profile,
        ).select_related("patient").order_by("-created_at")[:5]

    context = {
        "hospital": hospital,
        "doctor_profile": doctor_profile,
        "upcoming_appointments": upcoming_appointments,
        "total_consultations": total_consultations,
        "pending_labs_count": pending_labs_count,
        "recent_prescriptions": recent_prescriptions,
    }
    return render(request, "doctor/dashboard.html", context)


# ──────────────────────────────────────────────────────────────────────────────
# Receptionist Dashboard
# ──────────────────────────────────────────────────────────────────────────────

@receptionist_required
def receptionist_dashboard(request):
    from appointments.models import Appointment
    from patients.models import PatientProfile
    from billing.models import Invoice
    from laboratory.models import LabTestOrder

    hospital = get_user_hospital(request.user)

    context = {
        "hospital": hospital,
        "todays_appointments": Appointment.objects.filter(
            hospital=hospital,
            status__in=["PENDING", "CONFIRMED"],
        ).select_related("patient", "doctor").order_by("start_at")[:10],
        "recent_patients": PatientProfile.objects.filter(
            hospital=hospital,
        ).order_by("-created_at")[:5],
        "recent_invoices": Invoice.objects.filter(
            hospital=hospital,
        ).select_related("patient").order_by("-issued_at")[:5],
        "pending_lab_orders": LabTestOrder.objects.filter(
            hospital=hospital,
            status__in=["REQUESTED", "COLLECTED"],
        ).select_related("patient", "doctor").order_by("-ordered_at")[:5],
    }
    return render(request, "receptionist/dashboard.html", context)


# ──────────────────────────────────────────────────────────────────────────────
# Staff Dashboard
# ──────────────────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def staff_dashboard(request):
    return redirect("receptionist_dashboard")
