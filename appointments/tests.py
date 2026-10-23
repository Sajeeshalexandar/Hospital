from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from hospitals.models import Hospital
from departments.models import Department
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from appointments.models import Appointment
from appointments.forms import AppointmentBookingForm

User = get_user_model()


class AppointmentConflictTestCase(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name="Grace Memorial Hospital",
            registration_number="GMH-REG-001",
            email="info@gracememorial.com",
            phone="1122334455",
            address="789 Grace Blvd",
            city="Metropolis",
            state="Central",
        )
        self.dept = Department.objects.create(
            hospital=self.hospital,
            name="General Medicine",
        )
        self.doc_user = User.objects.create_user(
            username="dr_watson",
            email="watson@gracememorial.com",
            password="DocPassword@123",
            first_name="John",
            last_name="Watson",
        )
        self.doctor = DoctorProfile.objects.create(
            hospital=self.hospital,
            user=self.doc_user,
            department=self.dept,
            employee_code="DOC-WATSON-01",
            specialization="General Physician",
            consultation_fee=75.00,
        )
        self.patient_user = User.objects.create_user(
            username="sherlock_p",
            email="sherlock@bakerst.com",
            password="SherlockPassword@123",
            first_name="Sherlock",
            last_name="Holmes",
        )
        self.patient = PatientProfile.objects.create(
            hospital=self.hospital,
            user=self.patient_user,
            patient_id_code="PAT-GMH-0001",
            date_of_birth="1985-01-06",
            gender="MALE",
        )

    def test_schedule_conflict_prevention_rule8(self):
        """Rule #8: Prevent overlapping doctor appointments."""
        base_time = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
        slot1_start = base_time
        slot1_end = base_time + timedelta(minutes=30)

        # Existing confirmed booking
        Appointment.objects.create(
            hospital=self.hospital,
            doctor=self.doctor,
            patient=self.patient,
            department=self.dept,
            start_at=slot1_start,
            end_at=slot1_end,
            status=Appointment.Status.CONFIRMED,
        )

        # Overlapping booking attempt (starts 15 minutes after slot1 begins)
        form_overlap = AppointmentBookingForm(
            data={
                "patient": self.patient.pk,
                "doctor": self.doctor.pk,
                "department": self.dept.pk,
                "start_at": (slot1_start + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M"),
                "end_at": (slot1_end + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M"),
                "reason_for_visit": "Follow up consultation",
            },
            hospital=self.hospital,
        )
        self.assertFalse(form_overlap.is_valid())
        self.assertTrue(any("Schedule Conflict" in err for err in form_overlap.non_field_errors()))

        # Non-overlapping booking attempt (starts after slot1 finishes)
        form_valid = AppointmentBookingForm(
            data={
                "patient": self.patient.pk,
                "doctor": self.doctor.pk,
                "department": self.dept.pk,
                "start_at": (slot1_end + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M"),
                "end_at": (slot1_end + timedelta(minutes=40)).strftime("%Y-%m-%dT%H:%M"),
                "reason_for_visit": "Afternoon checkup",
            },
            hospital=self.hospital,
        )
        self.assertTrue(form_valid.is_valid())
