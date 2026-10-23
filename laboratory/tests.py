from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from hospitals.models import Hospital
from departments.models import Department
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from laboratory.models import LabTestOrder, LabReport
from laboratory.views import _generate_report_number

User = get_user_model()


class LaboratoryWorkflowTestCase(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name="Apex Diagnostic Center",
            registration_number="APEX-REG-001",
            email="lab@apex.com",
            phone="9876543210",
            address="456 Lab Way",
            city="Metro",
            state="Central",
        )
        self.dept = Department.objects.create(
            hospital=self.hospital,
            name="Pathology",
        )
        self.doc_user = User.objects.create_user(
            username="dr_sarah",
            email="sarah@apex.com",
            password="DocPassword@123",
            first_name="Sarah",
            last_name="Connor",
        )
        self.doctor = DoctorProfile.objects.create(
            hospital=self.hospital,
            user=self.doc_user,
            department=self.dept,
            employee_code="DOC-APEX-001",
            specialization="Pathologist",
            consultation_fee=100.00,
        )
        self.patient_user = User.objects.create_user(
            username="alice_patient",
            email="alice@example.com",
            password="PatientPassword@123",
            first_name="Alice",
            last_name="Wonder",
        )
        self.patient = PatientProfile.objects.create(
            hospital=self.hospital,
            user=self.patient_user,
            patient_id_code="PAT-APEX-0001",
            date_of_birth="1995-08-20",
            gender="FEMALE",
        )

    def test_report_number_generation(self):
        rep_num1 = _generate_report_number(self.hospital)
        year = timezone.now().year
        self.assertEqual(rep_num1, f"LAB-{year}-0001")

    def test_lab_order_and_completion_flow(self):
        order = LabTestOrder.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            doctor=self.doctor,
            test_name="Lipid Profile & Glucose",
            status=LabTestOrder.Status.REQUESTED,
        )
        self.assertEqual(order.status, LabTestOrder.Status.REQUESTED)

        # Transition order to COLLECTED then PROCESSING
        order.status = LabTestOrder.Status.COLLECTED
        order.save()
        self.assertEqual(order.status, LabTestOrder.Status.COLLECTED)

        order.status = LabTestOrder.Status.PROCESSING
        order.save()
        self.assertEqual(order.status, LabTestOrder.Status.PROCESSING)

        # Upload report
        report = LabReport.objects.create(
            hospital=self.hospital,
            order=order,
            patient=self.patient,
            report_number="LAB-2026-9999",
            result_summary="Total Cholesterol: 180 mg/dL (Normal: <200)\nTriglycerides: 140 mg/dL (Normal: <150)",
            tested_at=timezone.now(),
            reported_at=timezone.now(),
            verified_by=self.doc_user,
        )
        order.status = LabTestOrder.Status.COMPLETED
        order.save()

        order.refresh_from_db()
        self.assertEqual(order.status, LabTestOrder.Status.COMPLETED)
        self.assertEqual(order.reports.first().pk, report.pk)
