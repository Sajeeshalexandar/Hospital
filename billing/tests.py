from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model

from hospitals.models import Hospital
from memberships.models import HospitalMembership
from patients.models import PatientProfile
from billing.models import Invoice, InvoiceItem, Payment
from billing.views import _generate_invoice_number, _recalculate_invoice

User = get_user_model()


class BillingCalculationTestCase(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name="City General Hospital",
            registration_number="HOSP-REG-001",
            email="admin@citygen.com",
            phone="1234567890",
            address="123 Health Ave",
            city="Metropolis",
            state="Central",
        )
        self.patient_user = User.objects.create_user(
            username="john_patient",
            email="john@example.com",
            password="Password@123",
            first_name="John",
            last_name="Doe",
        )
        self.patient = PatientProfile.objects.create(
            hospital=self.hospital,
            user=self.patient_user,
            patient_id_code="PAT-2026-0001",
            date_of_birth="1988-05-15",
            gender="MALE",
        )
        self.admin_user = User.objects.create_user(
            username="city_admin",
            email="admin@citygen.com",
            password="AdminPassword@123",
        )
        HospitalMembership.objects.create(
            user=self.admin_user,
            hospital=self.hospital,
            role="HOSPITAL_ADMIN",
            is_active=True,
        )

    def test_invoice_number_generation(self):
        inv_num1 = _generate_invoice_number(self.hospital)
        year = timezone.now().year
        self.assertEqual(inv_num1, f"INV-{year}-0001")

        Invoice.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            invoice_number=inv_num1,
        )
        inv_num2 = _generate_invoice_number(self.hospital)
        self.assertEqual(inv_num2, f"INV-{year}-0002")

    def test_server_side_arithmetic_rule9(self):
        """Rule #9: Backend strictly computes subtotal, item totals, discounts, taxes, and final total."""
        invoice = Invoice.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            invoice_number="INV-2026-0010",
            discount_amount=Decimal("15.00"),
            tax_amount=Decimal("10.00"),
            status=Invoice.Status.DRAFT,
        )

        # Item 1: Consultation: 1 x 200 - 20 (disc) + 10 (tax) = 190
        item1 = InvoiceItem.objects.create(
            invoice=invoice,
            description="Cardiology Consultation",
            item_type=InvoiceItem.ItemType.CONSULTATION,
            quantity=Decimal("1.00"),
            unit_price=Decimal("200.00"),
            discount_amount=Decimal("20.00"),
            tax_amount=Decimal("10.00"),
            line_total=Decimal("190.00"),
        )

        # Item 2: ECG: 1 x 50 - 0 (disc) + 0 (tax) = 50
        item2 = InvoiceItem.objects.create(
            invoice=invoice,
            description="ECG Test",
            item_type=InvoiceItem.ItemType.PROCEDURE,
            quantity=Decimal("1.00"),
            unit_price=Decimal("50.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            line_total=Decimal("50.00"),
        )

        _recalculate_invoice(invoice)
        invoice.refresh_from_db()

        # Subtotal: (1 * 200) + (1 * 50) = 250.00
        self.assertEqual(invoice.subtotal, Decimal("250.00"))
        # Line totals sum: 190 + 50 = 240.00
        # Final Total: 240.00 - 15.00 (inv disc) + 10.00 (inv tax) = 235.00
        self.assertEqual(invoice.total_amount, Decimal("235.00"))
        self.assertEqual(invoice.status, Invoice.Status.ISSUED)

    def test_payment_status_transitions(self):
        """Payments transition status from ISSUED -> PARTIALLY_PAID -> PAID."""
        invoice = Invoice.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            invoice_number="INV-2026-0020",
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            status=Invoice.Status.ISSUED,
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="General OPD",
            unit_price=Decimal("100.00"),
            quantity=Decimal("1.00"),
            line_total=Decimal("100.00"),
        )

        # Partial payment of $40
        p1 = Payment.objects.create(
            invoice=invoice,
            amount=Decimal("40.00"),
            payment_method=Payment.Method.CASH,
            status=Payment.Status.COMPLETED,
            received_by=self.admin_user,
        )
        _recalculate_invoice(invoice)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PARTIALLY_PAID)

        # Remaining payment of $60
        p2 = Payment.objects.create(
            invoice=invoice,
            amount=Decimal("60.00"),
            payment_method=Payment.Method.CARD,
            status=Payment.Status.COMPLETED,
            received_by=self.admin_user,
        )
        _recalculate_invoice(invoice)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PAID)
