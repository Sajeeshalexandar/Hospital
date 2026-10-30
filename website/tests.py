from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from hospitals.models import Hospital
from departments.models import Department
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from appointments.models import Appointment
from memberships.models import HospitalMembership
from notifications.models import Notification

User = get_user_model()


class WebsiteAndPortalTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Hospital
        self.hospital = Hospital.objects.create(
            name="Apollo Test Hospital",
            registration_number="HOSP-TEST-001",
            email="info@apollotest.com",
            phone="+91 22 2847 0000",
            address="Test Park",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400076",
        )

        # 2. Department
        self.dept = Department.objects.create(
            hospital=self.hospital,
            name="Cardiology",
            description="Heart care",
        )

        # 3. Doctor User & Profile
        self.doctor_user = User.objects.create_user(
            username="dr.test@apollo.com",
            email="dr.test@apollo.com",
            password="DoctorPass@123",
            first_name="Ramesh",
            last_name="Gupta",
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            department=self.dept,
            employee_code="DOC-APO-001",
            qualification="MBBS, MD (Cardio)",
            specialization="Interventional Cardiology",
            experience_years=12,
            consultation_fee=Decimal("800.00"),
            contact_number="+91 98200 11111",
        )
        HospitalMembership.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            role="DOCTOR",
            is_active=True,
        )

        # 4. Receptionist
        self.reception_user = User.objects.create_user(
            username="priya.test@apollo.com",
            email="priya.test@apollo.com",
            password="StaffPass@123",
            first_name="Priya",
            last_name="Sharma",
        )
        HospitalMembership.objects.create(
            user=self.reception_user,
            hospital=self.hospital,
            role="RECEPTIONIST",
            is_active=True,
        )

        # 5. Hospital Admin
        self.hosp_admin_user = User.objects.create_user(
            username="admin.test@apollo.com",
            email="admin.test@apollo.com",
            password="AdminPass@123",
            first_name="Admin",
            last_name="Apollo",
        )
        HospitalMembership.objects.create(
            user=self.hosp_admin_user,
            hospital=self.hospital,
            role="HOSPITAL_ADMIN",
            is_active=True,
        )

        # 6. Super Admin
        self.superadmin = User.objects.create_superuser(
            username="super.test@medisaas.com",
            email="super.test@medisaas.com",
            password="SuperPass@123",
        )

    def test_landing_page_loads(self):
        """Landing page renders successfully with patient website elements."""
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MediSaaS Healthcare")
        self.assertContains(response, "Apollo Test Hospital")
        self.assertContains(response, "Dr. Ramesh Gupta")

    def test_doctors_directory(self):
        """Doctor directory renders and filters properly."""
        response = self.client.get(reverse("doctors_directory"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Ramesh Gupta")
        self.assertContains(response, "Interventional Cardiology")

    def test_services_page(self):
        """Clinical specialties page renders departments."""
        response = self.client.get(reverse("services_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cardiology")

    def test_portals_gateway_page(self):
        """Portals directory displays separate logins for Doctor, Receptionist, Hospital Admin, Super Admin."""
        response = self.client.get(reverse("portals_gateway"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Doctor Portal")
        self.assertContains(response, "Receptionist Desk")
        self.assertContains(response, "Hospital Admin")
        self.assertContains(response, "Super Admin")

    def test_online_appointment_booking(self):
        """Patient can book an online appointment via public website."""
        tomorrow = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "hospital": self.hospital.id,
            "department": self.dept.id,
            "doctor": self.doctor_profile.id,
            "appointment_date": tomorrow,
            "appointment_time": "14:00",
            "first_name": "Arjun",
            "last_name": "Kumar",
            "phone": "+91 98989 77777",
            "email": "arjun@example.com",
            "gender": "MALE",
            "reason": "Chest pain review",
        }
        response = self.client.post(reverse("book_appointment"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appointment Scheduled Successfully")
        self.assertTrue(Appointment.objects.filter(doctor=self.doctor_profile, patient__user__first_name="Arjun").exists())

    def test_patient_portal_lookup(self):
        """Patient can lookup their records via Patient ID code."""
        # Book an appointment first to establish patient
        patient_user = User.objects.create_user(username="pat_test", email="pat@test.com", first_name="Sneha", last_name="Roy")
        PatientProfile.objects.create(
            hospital=self.hospital,
            user=patient_user,
            patient_id_code="PAT-2026-9999",
            date_of_birth=timezone.now().date() - timedelta(days=365*30),
            gender="FEMALE",
            contact_number="+91 99999 88888",
            address="Test Street",
        )
        response = self.client.get(reverse("patient_portal") + "?q=PAT-2026-9999")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sneha Roy")
        self.assertContains(response, "PAT-2026-9999")

    def test_role_login_pages(self):
        """All dedicated role login pages load with correct role branding."""
        for url_name, expected_badge in [
            ("doctor_login", "Doctor Access"),
            ("receptionist_login", "Receptionist Access"),
            ("hospital_admin_login", "Hospital Admin Access"),
            ("super_admin_login", "Super Admin Access"),
            ("staff_login", "Staff Access"),
            ("patient_login", "Patient Access"),
        ]:
            resp = self.client.get(reverse(url_name))
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, expected_badge)

    def test_generic_login_url_redirects_to_portal_directory(self):
        response = self.client.get(reverse("login"))

        self.assertRedirects(
            response,
            reverse("portals_gateway"),
            fetch_redirect_response=False,
        )

    def test_anonymous_role_dashboard_redirects_to_matching_login_page(self):
        role_routes = [
            ("doctor_dashboard", "doctor_login"),
            ("receptionist_dashboard", "receptionist_login"),
            ("hospital_admin_dashboard", "hospital_admin_login"),
            ("super_admin_dashboard", "super_admin_login"),
            ("staff_dashboard", "staff_login"),
            ("patient_dashboard", "patient_login"),
        ]
        for dashboard_url, login_url in role_routes:
            response = self.client.get(reverse(dashboard_url))
            self.assertRedirects(
                response,
                reverse(login_url),
                fetch_redirect_response=False,
                msg_prefix=f"{dashboard_url} should redirect to {login_url}",
            )

    def test_logout_returns_to_same_role_login_page(self):
        self.client.force_login(self.doctor_user)

        response = self.client.get(reverse("logout"))

        self.assertRedirects(
            response,
            reverse("doctor_login"),
            fetch_redirect_response=False,
        )

    def test_role_login_routes_to_authorized_dashboard(self):
        """Each role-specific login accepts matching credentials and opens its dashboard."""
        password = "RoleLoginTest123!"
        patient_user = User.objects.create_user(
            username="patient.route@test.com",
            email="patient.route@test.com",
        )
        PatientProfile.objects.create(
            hospital=self.hospital,
            user=patient_user,
            patient_id_code="PAT-ROUTE-001",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="FEMALE",
            contact_number="+91 99999 88888",
            address="Test Street",
        )
        staff_user = User.objects.create_user(
            username="staff.route@test.com",
            email="staff.route@test.com",
        )
        HospitalMembership.objects.create(
            user=staff_user,
            hospital=self.hospital,
            role="STAFF",
            is_active=True,
        )
        role_users = [
            ("doctor_login", "doctor_dashboard", self.doctor_user),
            ("receptionist_login", "receptionist_dashboard", self.reception_user),
            ("hospital_admin_login", "hospital_admin_dashboard", self.hosp_admin_user),
            ("super_admin_login", "super_admin_dashboard", self.superadmin),
            ("staff_login", "staff_dashboard", staff_user),
            ("patient_login", "patient_dashboard", patient_user),
        ]

        for login_url, dashboard_url, user in role_users:
            user.set_password(password)
            user.save(update_fields=["password"])
            response = self.client.post(
                reverse(login_url),
                {"email": user.email, "password": password},
            )
            self.assertRedirects(
                response,
                reverse(dashboard_url),
                fetch_redirect_response=False,
                msg_prefix=f"{login_url} should route to {dashboard_url}",
            )
            dashboard_response = self.client.get(response.url)
            self.assertEqual(
                dashboard_response.status_code,
                200,
                msg=f"{dashboard_url} should allow its matching account",
            )
            self.client.logout()

    def test_role_login_rejects_credentials_for_another_role(self):
        """A valid account of another role stays on the selected portal with an error."""
        password = "RoleLoginTest123!"
        self.doctor_user.set_password(password)
        self.doctor_user.save(update_fields=["password"])

        response = self.client.post(
            reverse("receptionist_login"),
            {"email": self.doctor_user.email, "password": password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have access to the Receptionist Access portal")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_role_login_page_is_available_for_another_signed_in_role(self):
        """Selecting a different portal should show its login page, not dispatch the current session."""
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("hospital_admin_login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospital Admin Access")

    def test_patient_dashboard_loads_notifications(self):
        """Patient dashboard filters notifications by the Notification.user field."""
        patient_user = User.objects.create_user(
            username="patient.dashboard@test.com",
            email="patient.dashboard@test.com",
        )
        patient = PatientProfile.objects.create(
            hospital=self.hospital,
            user=patient_user,
            patient_id_code="PAT-DASH-001",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="FEMALE",
            contact_number="+91 99999 88888",
            address="Test Street",
        )
        notification = Notification.objects.create(
            user=patient_user,
            hospital=self.hospital,
            title="Appointment reminder",
            message="Your appointment is tomorrow.",
        )
        self.client.force_login(patient_user)

        response = self.client.get(reverse("patient_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["notifications"]), [notification])

    def test_hospital_admin_analytics(self):
        """Hospital admin analytics & assessment page loads with KPIs."""
        self.client.force_login(self.hosp_admin_user)
        response = self.client.get(reverse("hospital_admin_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospital Operational Assessment & Analytics")
        self.assertContains(response, "COMPOSITE HEALTH INDEX")

    def test_super_admin_analytics(self):
        """Super admin analytics & assessment page loads with platform telemetry."""
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("super_admin_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SaaS Platform Assessment & Multi-Tenant Analytics")
        self.assertContains(response, "ESTIMATED MRR")
