from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q

from accounts.decorators import roles_required
from accounts.helpers import get_user_hospital
from audit_logs.utils import log_audit
from notifications.utils import create_notification
from .models import Invoice, InvoiceItem, Payment
from .forms import InvoiceForm, InvoiceItemForm, PaymentForm


def _generate_invoice_number(hospital):
    """Auto-generate sequential invoice number: INV-YYYY-0001."""
    year = timezone.now().year
    prefix = f"INV-{year}-"
    last_inv = (
        Invoice.objects.filter(hospital=hospital, invoice_number__startswith=prefix)
        .order_by("-id")
        .first()
    )
    if last_inv and last_inv.invoice_number:
        try:
            last_num = int(last_inv.invoice_number.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = Invoice.objects.filter(hospital=hospital).count() + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:04d}"


def _recalculate_invoice(invoice):
    """
    Strict server-side financial calculations (Rule #9).
    Line total = (quantity * unit_price) - discount_amount + tax_amount
    Subtotal = sum(item.quantity * item.unit_price)
    Total amount = sum(item.line_total) - invoice.discount_amount + invoice.tax_amount
    Balance due = total_amount - sum(completed_payments)
    """
    items = invoice.items.all()
    subtotal = sum((item.quantity * item.unit_price for item in items), Decimal("0.00"))
    line_sum = sum((item.line_total for item in items), Decimal("0.00"))

    invoice.subtotal = Decimal(str(subtotal)).quantize(Decimal("0.01"))

    inv_discount = invoice.discount_amount or Decimal("0.00")
    inv_tax = invoice.tax_amount or Decimal("0.00")
    total = line_sum - inv_discount + inv_tax
    invoice.total_amount = max(Decimal("0.00"), Decimal(str(total)).quantize(Decimal("0.01")))

    completed_payments = invoice.payments.filter(status=Payment.Status.COMPLETED)
    total_paid = sum((p.amount for p in completed_payments), Decimal("0.00"))

    if invoice.status != Invoice.Status.VOID:
        if invoice.total_amount > Decimal("0.00") and total_paid >= invoice.total_amount:
            invoice.status = Invoice.Status.PAID
        elif total_paid > Decimal("0.00"):
            invoice.status = Invoice.Status.PARTIALLY_PAID
        elif invoice.status == Invoice.Status.DRAFT and items.exists():
            invoice.status = Invoice.Status.ISSUED
        elif not items.exists() and total_paid == Decimal("0.00"):
            invoice.status = Invoice.Status.DRAFT

    invoice.save()
    return total_paid


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "STAFF", "DOCTOR")
def invoice_list(request):
    """List invoices with status filters, search, and financial metrics."""
    hospital = get_user_hospital(request.user)
    invoices = Invoice.objects.select_related(
        "patient", "patient__user", "appointment"
    ).filter(hospital=hospital).order_by("-issued_at")

    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()

    if status:
        invoices = invoices.filter(status=status)

    if q:
        invoices = invoices.filter(
            Q(invoice_number__icontains=q)
            | Q(patient__patient_id_code__icontains=q)
            | Q(patient__user__first_name__icontains=q)
            | Q(patient__user__last_name__icontains=q)
        )

    # Compute high-level financial summary
    all_hospital_invoices = Invoice.objects.filter(hospital=hospital)
    total_billed = all_hospital_invoices.exclude(status=Invoice.Status.VOID).aggregate(
        Sum("total_amount")
    )["total_amount__sum"] or Decimal("0.00")

    total_collected = Payment.objects.filter(
        invoice__hospital=hospital, status=Payment.Status.COMPLETED
    ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

    total_outstanding = max(Decimal("0.00"), total_billed - total_collected)

    context = {
        "hospital": hospital,
        "invoices": invoices,
        "status_choices": Invoice.Status.choices,
        "status_filter": status,
        "q": q,
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
    }
    return render(request, "billing/invoices/list.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "STAFF")
def invoice_create(request):
    """Create an invoice header."""
    hospital = get_user_hospital(request.user)
    form = InvoiceForm(request.POST or None, hospital=hospital)

    if request.method == "POST":
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.hospital = hospital
            if not invoice.invoice_number:
                invoice.invoice_number = _generate_invoice_number(hospital)
            invoice.status = Invoice.Status.DRAFT
            invoice.save()

            log_audit(
                request,
                "CREATE_INVOICE",
                "Invoice",
                invoice.pk,
                f"Generated invoice {invoice.invoice_number} for patient {invoice.patient.patient_id_code}",
                hospital=hospital,
            )

            messages.success(request, f"Invoice {invoice.invoice_number} generated. Add items below.")
            return redirect("invoice_detail", pk=invoice.pk)
        else:
            messages.error(request, "Please correct the errors in the invoice form.")

    context = {
        "form": form,
        "hospital": hospital,
    }
    return render(request, "billing/invoices/form.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "STAFF", "DOCTOR")
def invoice_detail(request, pk):
    """Interactive invoice detail workspace: items, payments, balance, and print sheet."""
    hospital = get_user_hospital(request.user)
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "patient", "patient__user", "appointment", "hospital"
        ).prefetch_related("items", "payments", "payments__received_by"),
        pk=pk,
        hospital=hospital,
    )

    completed_payments = invoice.payments.filter(status=Payment.Status.COMPLETED)
    total_paid = sum((p.amount for p in completed_payments), Decimal("0.00"))
    balance_due = max(Decimal("0.00"), invoice.total_amount - total_paid)

    item_form = InvoiceItemForm()
    payment_form = PaymentForm(initial={"amount": balance_due})

    context = {
        "hospital": hospital,
        "invoice": invoice,
        "items": invoice.items.all(),
        "payments": invoice.payments.all().order_by("-paid_at"),
        "total_paid": total_paid,
        "balance_due": balance_due,
        "item_form": item_form,
        "payment_form": payment_form,
        "is_print": request.GET.get("print") == "1",
    }
    return render(request, "billing/invoices/detail.html", context)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "STAFF")
def invoice_item_add(request, pk):
    """Add a billable line item with server-side arithmetic."""
    hospital = get_user_hospital(request.user)
    invoice = get_object_or_404(Invoice, pk=pk, hospital=hospital)

    if invoice.status == Invoice.Status.VOID:
        messages.error(request, "Cannot add items to a void invoice.")
        return redirect("invoice_detail", pk=invoice.pk)

    if request.method == "POST":
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice

            # Server-side calculation of line_total (Rule #9)
            qty = item.quantity or Decimal("1")
            price = item.unit_price or Decimal("0.00")
            disc = item.discount_amount or Decimal("0.00")
            tax = item.tax_amount or Decimal("0.00")

            raw_total = (qty * price) - disc + tax
            item.line_total = max(Decimal("0.00"), Decimal(str(raw_total)).quantize(Decimal("0.01")))
            item.save()

            _recalculate_invoice(invoice)

            log_audit(
                request,
                "ADD_INVOICE_ITEM",
                "InvoiceItem",
                item.pk,
                f"Added item '{item.description}' ({item.line_total}) to invoice {invoice.invoice_number}",
                hospital=hospital,
            )

            messages.success(request, f"Item '{item.description}' added successfully.")
        else:
            messages.error(request, "Error adding item. Please review the item fields.")

    return redirect("invoice_detail", pk=invoice.pk)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "STAFF")
def invoice_item_delete(request, invoice_pk, pk):
    """Remove a line item and recalculate totals."""
    hospital = get_user_hospital(request.user)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, hospital=hospital)
    item = get_object_or_404(InvoiceItem, pk=pk, invoice=invoice)

    if invoice.status == Invoice.Status.VOID:
        messages.error(request, "Cannot modify a void invoice.")
        return redirect("invoice_detail", pk=invoice.pk)

    item_desc = item.description
    item.delete()
    _recalculate_invoice(invoice)

    log_audit(
        request,
        "DELETE_INVOICE_ITEM",
        "InvoiceItem",
        pk,
        f"Removed item '{item_desc}' from invoice {invoice.invoice_number}",
        hospital=hospital,
    )

    messages.success(request, f"Item '{item_desc}' removed.")
    return redirect("invoice_detail", pk=invoice.pk)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST", "STAFF")
def payment_record(request, pk):
    """Record customer payment and progress invoice status."""
    hospital = get_user_hospital(request.user)
    invoice = get_object_or_404(Invoice, pk=pk, hospital=hospital)

    if invoice.status == Invoice.Status.VOID:
        messages.error(request, "Cannot accept payment for a void invoice.")
        return redirect("invoice_detail", pk=invoice.pk)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.status = Payment.Status.COMPLETED
            payment.received_by = request.user
            payment.paid_at = timezone.now()
            payment.save()

            _recalculate_invoice(invoice)

            log_audit(
                request,
                "RECORD_PAYMENT",
                "Payment",
                payment.pk,
                f"Collected {payment.amount} via {payment.get_payment_method_display()} for invoice {invoice.invoice_number}",
                hospital=hospital,
            )

            # In-app notification to patient user if exists
            if invoice.patient.user:
                create_notification(
                    invoice.patient.user,
                    "Payment Received",
                    f"Payment of {payment.amount} received for invoice {invoice.invoice_number}.",
                    hospital=hospital,
                    notification_type="PAYMENT",
                )

            messages.success(request, f"Payment of {payment.amount} recorded successfully.")
        else:
            messages.error(request, "Failed to record payment. Please check payment amount.")

    return redirect("invoice_detail", pk=invoice.pk)


@roles_required("HOSPITAL_ADMIN", "RECEPTIONIST")
def invoice_status_update(request, pk):
    """Change invoice status (e.g. mark ISSUED or VOID)."""
    hospital = get_user_hospital(request.user)
    invoice = get_object_or_404(Invoice, pk=pk, hospital=hospital)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in Invoice.Status.values:
            old_status = invoice.status
            invoice.status = new_status
            invoice.save()

            log_audit(
                request,
                "UPDATE_INVOICE_STATUS",
                "Invoice",
                invoice.pk,
                f"Changed invoice {invoice.invoice_number} status from {old_status} to {new_status}",
                hospital=hospital,
            )

            messages.success(request, f"Invoice status changed to '{invoice.get_status_display()}'.")

    return redirect("invoice_detail", pk=invoice.pk)
