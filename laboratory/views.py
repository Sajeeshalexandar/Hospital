from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from accounts.decorators import roles_required
from accounts.helpers import get_user_hospital, get_user_role
from audit_logs.utils import log_audit
from notifications.utils import create_notification
from .models import LabTestOrder, LabReport
from .forms import LabTestOrderForm, LabReportForm


def _generate_report_number(hospital):
    """Auto-generate sequential lab report number: LAB-YYYY-0001."""
    year = timezone.now().year
    prefix = f"LAB-{year}-"
    last_rep = (
        LabReport.objects.filter(hospital=hospital, report_number__startswith=prefix)
        .order_by("-id")
        .first()
    )
    if last_rep and last_rep.report_number:
        try:
            last_num = int(last_rep.report_number.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = LabReport.objects.filter(hospital=hospital).count() + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST", "STAFF")
def order_list(request):
    """List lab test orders with status filters and search."""
    hospital = get_user_hospital(request.user)
    orders = LabTestOrder.objects.select_related(
        "patient", "patient__user", "doctor", "doctor__user", "appointment"
    ).filter(hospital=hospital).order_by("-ordered_at")

    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()

    if status:
        orders = orders.filter(status=status)

    if q:
        orders = orders.filter(
            test_name__icontains=q
        ) | orders.filter(
            patient__patient_id_code__icontains=q
        ) | orders.filter(
            patient__user__first_name__icontains=q
        )

    context = {
        "hospital": hospital,
        "orders": orders,
        "status_choices": LabTestOrder.Status.choices,
        "status_filter": status,
        "q": q,
    }
    return render(request, "laboratory/orders/list.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST")
def order_create(request):
    """Order a diagnostic laboratory investigation."""
    hospital = get_user_hospital(request.user)
    form = LabTestOrderForm(request.POST or None, hospital=hospital)

    if request.method == "POST":
        if form.is_valid():
            order = form.save(commit=False)
            order.hospital = hospital
            order.status = LabTestOrder.Status.REQUESTED
            order.save()

            log_audit(
                request,
                "ORDER_LAB_TEST",
                "LabTestOrder",
                order.pk,
                f"Ordered test '{order.test_name}' for patient {order.patient.patient_id_code}",
                hospital=hospital,
            )

            messages.success(request, f"Lab order for '{order.test_name}' registered successfully.")
            return redirect("lab_order_list")
        else:
            messages.error(request, "Please fix the errors in the form.")

    context = {"form": form, "hospital": hospital}
    return render(request, "laboratory/orders/form.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "STAFF")
def order_status_update(request, pk):
    """Advance lab order stage (COLLECTED, PROCESSING, CANCELLED)."""
    hospital = get_user_hospital(request.user)
    order = get_object_or_404(LabTestOrder, pk=pk, hospital=hospital)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in LabTestOrder.Status.values:
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to '{order.get_status_display()}'.")

    return redirect("lab_order_list")


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "STAFF")
def report_upload(request, pk):
    """Upload lab report results and file attachment."""
    hospital = get_user_hospital(request.user)
    order = get_object_or_404(LabTestOrder, pk=pk, hospital=hospital)
    form = LabReportForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            report = form.save(commit=False)
            report.order = order
            report.hospital = hospital
            report.patient = order.patient
            report.verified_by = request.user

            if not report.report_number:
                report.report_number = _generate_report_number(hospital)

            if not report.reported_at:
                report.reported_at = timezone.now()

            report.save()

            # Advance parent order status to COMPLETED
            order.status = LabTestOrder.Status.COMPLETED
            order.save()

            log_audit(
                request,
                "UPLOAD_LAB_REPORT",
                "LabReport",
                report.pk,
                f"Uploaded report {report.report_number} for test '{order.test_name}'",
                hospital=hospital,
            )

            # Notify doctor
            if order.doctor.user:
                create_notification(
                    order.doctor.user,
                    "Lab Report Ready",
                    f"Report {report.report_number} for patient {order.patient.patient_id_code} ({order.test_name}) is now available.",
                    hospital=hospital,
                    notification_type="LAB_RESULT",
                )

            messages.success(request, f"Lab report {report.report_number} published successfully.")
            return redirect("lab_report_detail", pk=report.pk)
        else:
            messages.error(request, "Could not save report. Please review the form.")

    context = {
        "form": form,
        "order": order,
        "hospital": hospital,
    }
    return render(request, "laboratory/reports/upload.html", context)


@roles_required("HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST", "STAFF")
def report_detail(request, pk):
    """Detailed view of laboratory report findings and attachments."""
    hospital = get_user_hospital(request.user)
    report = get_object_or_404(
        LabReport.objects.select_related("order", "patient", "patient__user", "verified_by", "hospital"),
        pk=pk,
        hospital=hospital,
    )
    context = {"report": report, "hospital": hospital}
    return render(request, "laboratory/reports/detail.html", context)
