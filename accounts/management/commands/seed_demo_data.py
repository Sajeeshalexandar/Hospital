import os
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from hospitals.models import HospitalTemplate, Hospital, HospitalSettings
from subscriptions.models import SubscriptionPlan, HospitalSubscription
from memberships.models import HospitalMembership
from departments.models import Department
from doctors.models import DoctorProfile, DoctorAvailability
from staff.models import StaffProfile
from patients.models import PatientProfile
from appointments.models import Appointment
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription, PrescriptionMedicine
from laboratory.models import LabTestOrder, LabReport
from billing.models import Invoice, InvoiceItem, Payment
from billing.views import _recalculate_invoice
from notifications.utils import create_notification
from audit_logs.models import AuditLog

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with realistic multi-tenant demonstration data for all 4 roles"

    def _set_demo_membership(self, user, hospital, role):
        HospitalMembership.objects.filter(
            user=user,
            is_active=True,
        ).exclude(hospital=hospital).update(is_active=False)
        return HospitalMembership.objects.update_or_create(
            user=user,
            hospital=hospital,
            defaults={"role": role, "is_active": True},
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding MediSaaS demo dataset..."))

        # 1. Super Admin
        super_admin, _ = User.objects.get_or_create(
            email="superadmin@medisaas.com",
            defaults={
                "username": "superadmin@medisaas.com",
                "first_name": "SaaS",
                "last_name": "SuperAdmin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        super_admin.set_password("SuperAdminPass@123")
        super_admin.save()
        self.stdout.write(self.style.SUCCESS(f"[User] Super Admin: superadmin@medisaas.com / SuperAdminPass@123"))

        # 2. Subscription Plans
        plan_standard, _ = SubscriptionPlan.objects.get_or_create(
            code="standard-care",
            defaults={
                "name": "Standard Care",
                "price": Decimal("4999.00"),
                "currency": "INR",
                "duration_days": 30,
                "max_users": 10,
                "max_patients": 1000,
                "features": {"billing": True, "appointments": True},
            },
        )
        plan_enterprise, _ = SubscriptionPlan.objects.get_or_create(
            code="enterprise-hospital",
            defaults={
                "name": "Enterprise Hospital",
                "price": Decimal("19999.00"),
                "currency": "INR",
                "duration_days": 365,
                "max_users": 100,
                "max_patients": 50000,
                "features": {"billing": True, "appointments": True, "laboratory": True, "audit": True},
            },
        )

        # 3. Hospital Template
        template_modern, _ = HospitalTemplate.objects.get_or_create(
            template_code="MODERN_BLUE",
            defaults={
                "name": "Modern Medical Blue",
                "description": "Professional high-contrast blue theme for clinical institutes.",
            },
        )

        # 4. Hospitals
        apollo, _ = Hospital.objects.get_or_create(
            registration_number="HOSP-APOLLO-001",
            defaults={
                "name": "Apollo Life Care",
                "email": "contact@apollocare.com",
                "phone": "+91 22 2847 9000",
                "address": "Plot 14, Health Park, Powai",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "postal_code": "400076",
                "template": template_modern,
                "status": Hospital.Status.ACTIVE,
            },
        )
        HospitalSettings.objects.get_or_create(
            hospital=apollo,
            defaults={"timezone": "Asia/Kolkata", "currency": "INR", "appointment_duration_minutes": 30},
        )

        metro, _ = Hospital.objects.get_or_create(
            registration_number="HOSP-METRO-002",
            defaults={
                "name": "Metro Health Institute",
                "email": "info@metrohealth.com",
                "phone": "+91 80 4123 5678",
                "address": "45 Brigade Road",
                "city": "Bangalore",
                "state": "Karnataka",
                "country": "India",
                "postal_code": "560001",
                "template": template_modern,
                "status": Hospital.Status.ACTIVE,
            },
        )

        # Subscriptions
        HospitalSubscription.objects.get_or_create(
            hospital=apollo,
            defaults={
                "plan": plan_enterprise,
                "start_date": timezone.now() - timedelta(days=30),
                "end_date": timezone.now() + timedelta(days=335),
                "status": "ACTIVE",
            },
        )

        # 5. Departments
        cardiology, _ = Department.objects.get_or_create(
            hospital=apollo,
            name="Cardiology",
            defaults={"description": "Cardiac care and non-invasive electrophysiology."},
        )
        general_med, _ = Department.objects.get_or_create(
            hospital=apollo,
            name="General Medicine",
            defaults={"description": "Outpatient primary care and chronic conditions."},
        )
        pathology, _ = Department.objects.get_or_create(
            hospital=apollo,
            name="Pathology & Laboratory",
            defaults={"description": "Hematology, biochemistry, and diagnostics."},
        )

        # 6. Hospital Admin
        apollo_admin_user, _ = User.objects.get_or_create(
            email="apollo.admin@medisaas.com",
            defaults={
                "username": "apollo.admin@medisaas.com",
                "first_name": "Vikram",
                "last_name": "Mehta",
            },
        )
        apollo_admin_user.set_password("AdminPass@123")
        apollo_admin_user.save()
        self._set_demo_membership(apollo_admin_user, apollo, HospitalMembership.Role.HOSPITAL_ADMIN)
        self.stdout.write(self.style.SUCCESS(f"[User] Hospital Admin: apollo.admin@medisaas.com / AdminPass@123"))

        # 7. Doctors
        doc1_user, _ = User.objects.get_or_create(
            email="dr.ramesh@apollo.com",
            defaults={
                "username": "dr.ramesh@apollo.com",
                "first_name": "Ramesh",
                "last_name": "Kumar",
            },
        )
        doc1_user.set_password("DoctorPass@123")
        doc1_user.save()
        self._set_demo_membership(doc1_user, apollo, HospitalMembership.Role.DOCTOR)
        DoctorProfile.objects.filter(
            user=doc1_user,
            is_active=True,
        ).exclude(hospital=apollo).update(is_active=False)
        dr_ramesh, _ = DoctorProfile.objects.update_or_create(
            hospital=apollo,
            employee_code="DOC-APOLLO-001",
            defaults={
                "user": doc1_user,
                "department": cardiology,
                "qualification": "MBBS, MD, DM (Cardiology)",
                "specialization": "Interventional Cardiologist",
                "experience_years": 14,
                "consultation_fee": Decimal("150.00"),
                "op_commission_percentage": Decimal("15.00"),
                "contact_number": "+91 98200 11223",
                "is_active": True,
            },
        )
        DoctorAvailability.objects.update_or_create(
            doctor=dr_ramesh,
            weekday=timezone.now().weekday(),
            defaults={
                "start_time": "09:00:00",
                "end_time": "17:00:00",
            },
        )
        self.stdout.write(self.style.SUCCESS(f"[User] Doctor: dr.ramesh@apollo.com / DoctorPass@123"))

        doc2_user, _ = User.objects.get_or_create(
            email="dr.anita@apollo.com",
            defaults={
                "username": "dr.anita@apollo.com",
                "first_name": "Anita",
                "last_name": "Deshmukh",
            },
        )
        doc2_user.set_password("DoctorPass@123")
        doc2_user.save()
        self._set_demo_membership(doc2_user, apollo, HospitalMembership.Role.DOCTOR)
        DoctorProfile.objects.filter(
            user=doc2_user,
            is_active=True,
        ).exclude(hospital=apollo).update(is_active=False)
        dr_anita, _ = DoctorProfile.objects.update_or_create(
            hospital=apollo,
            employee_code="DOC-APOLLO-002",
            defaults={
                "user": doc2_user,
                "department": general_med,
                "qualification": "MBBS, DNB (Internal Medicine)",
                "specialization": "Consultant Physician",
                "experience_years": 9,
                "consultation_fee": Decimal("100.00"),
                "op_commission_percentage": Decimal("10.00"),
                "contact_number": "+91 98200 33445",
                "is_active": True,
            },
        )
        DoctorAvailability.objects.update_or_create(
            doctor=dr_anita,
            weekday=timezone.now().weekday(),
            defaults={
                "start_time": "10:00:00",
                "end_time": "18:00:00",
            },
        )

        # 8. Receptionist
        receptionist_user, _ = User.objects.get_or_create(
            email="priya.reception@apollo.com",
            defaults={
                "username": "priya.reception@apollo.com",
                "first_name": "Priya",
                "last_name": "Nair",
            },
        )
        receptionist_user.set_password("StaffPass@123")
        receptionist_user.save()
        self._set_demo_membership(receptionist_user, apollo, HospitalMembership.Role.RECEPTIONIST)
        StaffProfile.objects.update_or_create(
            hospital=apollo,
            employee_code="STF-APOLLO-001",
            defaults={
                "user": receptionist_user,
                "job_title": "Senior Front Desk Executive",
                "contact_number": "+91 98200 55667",
                "date_of_joining": timezone.now().date() - timedelta(days=180),
                "is_active": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"[User] Receptionist: priya.reception@apollo.com / StaffPass@123"))

        # 9. Hospital Staff
        staff_user, _ = User.objects.get_or_create(
            email="staff.demo@apollo.com",
            defaults={
                "username": "staff.demo@apollo.com",
                "first_name": "Arjun",
                "last_name": "Rao",
            },
        )
        staff_user.set_password("StaffPass@123")
        staff_user.save()
        self._set_demo_membership(staff_user, apollo, HospitalMembership.Role.STAFF)
        StaffProfile.objects.update_or_create(
            hospital=apollo,
            employee_code="STF-APOLLO-002",
            defaults={
                "user": staff_user,
                "job_title": "Hospital Operations Assistant",
                "contact_number": "+91 98200 66778",
                "date_of_joining": timezone.now().date() - timedelta(days=90),
                "is_active": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"[User] Staff: staff.demo@apollo.com / StaffPass@123"))

        # 10. Patients
        patient1_user, _ = User.objects.get_or_create(
            email="anil.kapoor@example.com",
            defaults={
                "username": "anil.kapoor@example.com",
                "first_name": "Anil",
                "last_name": "Kapoor",
            },
        )
        patient1_user.set_password("PatientPass@123")
        patient1_user.save()
        PatientProfile.objects.filter(
            user=patient1_user,
            is_active=True,
        ).exclude(hospital=apollo).update(is_active=False)
        patient1, _ = PatientProfile.objects.update_or_create(
            hospital=apollo,
            patient_id_code="PAT-2026-0001",
            defaults={
                "user": patient1_user,
                "date_of_birth": "1975-04-12",
                "gender": PatientProfile.Gender.MALE,
                "blood_group": "O+",
                "contact_number": "+91 98111 22334",
                "address": "Flat 301, Palm Grove, Bandra",
                "emergency_contact_name": "Sunita Kapoor",
                "emergency_contact_number": "+91 98111 99887",
            },
        )

        patient2_user, _ = User.objects.get_or_create(
            email="sunita.patel@example.com",
            defaults={
                "username": "sunita.patel@example.com",
                "first_name": "Sunita",
                "last_name": "Patel",
            },
        )
        patient2_user.set_password("PatientPass@123")
        patient2_user.save()
        PatientProfile.objects.filter(
            user=patient2_user,
            is_active=True,
        ).exclude(hospital=apollo).update(is_active=False)
        patient2, _ = PatientProfile.objects.update_or_create(
            hospital=apollo,
            patient_id_code="PAT-2026-0002",
            defaults={
                "user": patient2_user,
                "date_of_birth": "1988-09-25",
                "gender": PatientProfile.Gender.FEMALE,
                "blood_group": "B+",
                "contact_number": "+91 98333 44556",
                "address": "B-12 Hill Crest, Andheri West",
                "emergency_contact_name": "Rahul Patel",
                "emergency_contact_number": "+91 98333 88776",
            },
        )

        # 10. Appointments
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        appt1, _ = Appointment.objects.update_or_create(
            hospital=apollo,
            doctor=dr_ramesh,
            patient=patient1,
            start_at=now - timedelta(days=2, hours=3),
            defaults={
                "department": cardiology,
                "end_at": now - timedelta(days=2, hours=2, minutes=30),
                "reason_for_visit": "Chest tightness on climbing stairs and palpitation review.",
                "status": Appointment.Status.COMPLETED,
                "created_by": receptionist_user,
            },
        )

        appt2, _ = Appointment.objects.update_or_create(
            hospital=apollo,
            doctor=dr_anita,
            patient=patient2,
            start_at=now + timedelta(days=1, hours=2),
            defaults={
                "department": general_med,
                "end_at": now + timedelta(days=1, hours=2, minutes=30),
                "reason_for_visit": "Persistent low-grade fever and dry cough for 4 days.",
                "status": Appointment.Status.CONFIRMED,
                "created_by": receptionist_user,
            },
        )

        # 11. Medical Record & Prescription for Appt 1
        med_rec, _ = MedicalRecord.objects.update_or_create(
            appointment=appt1,
            defaults={
                "hospital": apollo,
                "patient": patient1,
                "doctor": dr_ramesh,
                "diagnosis": "Grade 1 Essential Hypertension with mild sinus tachycardia",
                "treatment_notes": "Lifestyle modification, low sodium diet (<2g/day), daily walking 30 mins.",
                "symptoms": "Occasional exertional breathlessness, mild headache.",
                "created_by": doc1_user,
            },
        )

        rx, _ = Prescription.objects.update_or_create(
            hospital=apollo,
            prescription_number="RX-2026-0001",
            defaults={
                "appointment": appt1,
                "doctor": dr_ramesh,
                "patient": patient1,
                "status": Prescription.Status.ISSUED,
                "issued_at": now - timedelta(days=2, hours=2),
                "notes": "Review blood pressure log after 14 days. Avoid OTC decongestants.",
            },
        )
        PrescriptionMedicine.objects.get_or_create(
            prescription=rx,
            medicine_name="Amlodipine Besylate",
            defaults={
                "dosage": "5 mg",
                "frequency": "1-0-0 (Morning after food)",
                "duration": "30 days",
                "quantity": 30,
                "route": "ORAL",
            },
        )
        PrescriptionMedicine.objects.get_or_create(
            prescription=rx,
            medicine_name="Aspirin (Enteric Coated)",
            defaults={
                "dosage": "75 mg",
                "frequency": "0-0-1 (Night after dinner)",
                "duration": "30 days",
                "quantity": 30,
                "route": "ORAL",
            },
        )

        # 12. Laboratory Order & Report
        lab_order, _ = LabTestOrder.objects.update_or_create(
            hospital=apollo,
            appointment=appt1,
            test_name="Lipid Profile & Serum Electrolytes",
            defaults={
                "patient": patient1,
                "doctor": dr_ramesh,
                "clinical_notes": "Evaluate baseline lipid markers and potassium prior to ACEi therapy.",
                "status": LabTestOrder.Status.COMPLETED,
            },
        )
        LabReport.objects.update_or_create(
            hospital=apollo,
            report_number="LAB-2026-0001",
            defaults={
                "order": lab_order,
                "patient": patient1,
                "result_summary": (
                    "Total Cholesterol: 215 mg/dL [Desirable: <200]\n"
                    "HDL Cholesterol: 44 mg/dL [Normal: >40]\n"
                    "LDL Cholesterol: 138 mg/dL [Optimal: <100]\n"
                    "Serum Triglycerides: 165 mg/dL [Normal: <150]\n"
                    "Serum Potassium: 4.2 mmol/L [Normal: 3.5-5.0]"
                ),
                "remarks": "Borderline hyperlipidemia noted. Statin therapy advised if diet non-responsive.",
                "tested_at": now - timedelta(days=2, hours=1),
                "reported_at": now - timedelta(days=2),
                "verified_by": doc1_user,
            },
        )

        # 13. Billing Invoices
        # Invoice 1: Paid in Full
        inv1, _ = Invoice.objects.update_or_create(
            hospital=apollo,
            invoice_number="INV-2026-0001",
            defaults={
                "patient": patient1,
                "appointment": appt1,
                "due_date": (now - timedelta(days=2)).date(),
                "discount_amount": Decimal("10.00"),
                "tax_amount": Decimal("15.00"),
                "notes": "Full consultation and diagnostic panel.",
                "status": Invoice.Status.DRAFT,
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv1,
            description="Specialist Cardiology Consultation",
            defaults={
                "item_type": InvoiceItem.ItemType.CONSULTATION,
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("150.00"),
                "line_total": Decimal("150.00"),
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv1,
            description="Lipid Profile & Electrolyte Diagnostic Panel",
            defaults={
                "item_type": InvoiceItem.ItemType.LABORATORY,
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("120.00"),
                "line_total": Decimal("120.00"),
            },
        )
        _recalculate_invoice(inv1)

        Payment.objects.get_or_create(
            invoice=inv1,
            transaction_reference="CARD-TXN-APOLLO-001",
            defaults={
                "amount": inv1.total_amount,
                "payment_method": Payment.Method.CARD,
                "status": Payment.Status.COMPLETED,
                "paid_at": now - timedelta(days=2, hours=2),
                "received_by": receptionist_user,
            },
        )
        _recalculate_invoice(inv1)

        # Invoice 2: Partially Paid for Patient 2
        inv2, _ = Invoice.objects.update_or_create(
            hospital=apollo,
            invoice_number="INV-2026-0002",
            defaults={
                "patient": patient2,
                "appointment": appt2,
                "due_date": (now + timedelta(days=3)).date(),
                "discount_amount": Decimal("0.00"),
                "tax_amount": Decimal("5.00"),
                "notes": "Consultation advance collected.",
                "status": Invoice.Status.DRAFT,
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv2,
            description="General Physician Consultation",
            defaults={
                "item_type": InvoiceItem.ItemType.CONSULTATION,
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv2,
            description="Rapid Antigen & Vitals Screening",
            defaults={
                "item_type": InvoiceItem.ItemType.PROCEDURE,
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("50.00"),
                "line_total": Decimal("50.00"),
            },
        )
        _recalculate_invoice(inv2)

        Payment.objects.get_or_create(
            invoice=inv2,
            transaction_reference="CASH-REC-APOLLO-002",
            defaults={
                "amount": Decimal("75.00"),
                "payment_method": Payment.Method.CASH,
                "status": Payment.Status.COMPLETED,
                "paid_at": now,
                "received_by": receptionist_user,
            },
        )
        _recalculate_invoice(inv2)

        # 14. In-App Notifications
        create_notification(
            user=doc1_user,
            title="Lab Report Ready: Anil Kapoor",
            message="Diagnostic panel LAB-2026-0001 (Lipid Profile) is verified and ready for review.",
            hospital=apollo,
            notification_type="LAB_RESULT",
        )
        create_notification(
            user=doc2_user,
            title="New Patient Scheduled",
            message="Sunita Patel has booked a consultation for tomorrow at 12:00 PM.",
            hospital=apollo,
            notification_type="APPOINTMENT",
        )
        create_notification(
            user=apollo_admin_user,
            title="Payment Received",
            message="Collected $75.00 advance for invoice INV-2026-0002 (Sunita Patel).",
            hospital=apollo,
            notification_type="PAYMENT",
        )

        # 15. Security Audit Trail Entries
        AuditLog.objects.get_or_create(
            hospital=apollo,
            actor=receptionist_user,
            action="SCHEDULE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=str(appt2.pk),
            defaults={
                "description": "Booked consultation for patient PAT-2026-0002 with Dr. Anita Deshmukh",
                "ip_address": "127.0.0.1",
            },
        )
        AuditLog.objects.get_or_create(
            hospital=apollo,
            actor=doc1_user,
            action="ISSUE_PRESCRIPTION",
            entity_type="Prescription",
            entity_id=str(rx.pk),
            defaults={
                "description": "Digitally signed prescription RX-2026-0001 with 2 medicines",
                "ip_address": "127.0.0.1",
            },
        )
        AuditLog.objects.get_or_create(
            hospital=apollo,
            actor=receptionist_user,
            action="RECORD_PAYMENT",
            entity_type="Payment",
            entity_id="1",
            defaults={
                "description": "Settled invoice INV-2026-0001 in full ($275.00) via Card",
                "ip_address": "127.0.0.1",
            },
        )

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("DEMO DATASET SEEDED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("Credentials ready for testing:")
        self.stdout.write("  Super Admin:     superadmin@medisaas.com      / SuperAdminPass@123")
        self.stdout.write("  Hospital Admin:  apollo.admin@medisaas.com    / AdminPass@123")
        self.stdout.write("  Doctor:          dr.ramesh@apollo.com         / DoctorPass@123")
        self.stdout.write("  Receptionist:    priya.reception@apollo.com   / StaffPass@123")
        self.stdout.write("  Staff:           staff.demo@apollo.com         / StaffPass@123")
        self.stdout.write("  Patient:         anil.kapoor@example.com       / PatientPass@123")
