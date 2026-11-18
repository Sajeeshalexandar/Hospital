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
from staff.models import StaffProfile
from memberships.models import HospitalMembership

User = get_user_model()


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Hospital
        self.hospital = Hospital.objects.create(
            name="Apollo Life Care",
            registration_number="HOSP-APOLLO-TEST",
            email="contact@apollocare.test",
            phone="+91 22 2847 9000",
            address="Plot 14, Health Park",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400076",
        )

        # Department
        self.dept = Department.objects.create(
            hospital=self.hospital,
            name="Cardiology",
            description="Cardiac care",
        )

        # Standard password for test accounts
        self.password = "SecurePassword@2026"

        # 1. Super Admin
        self.super_admin = User.objects.create_superuser(
            username="superadmin@medisaas.com",
            email="superadmin@medisaas.com",
            password=self.password,
            first_name="SaaS",
            last_name="SuperAdmin",
        )

        # 2. Hospital Admin
        self.hospital_admin_user = User.objects.create_user(
            username="apollo.admin@medisaas.com",
            email="apollo.admin@medisaas.com",
            password=self.password,
            first_name="Vikram",
            last_name="Mehta",
        )
        HospitalMembership.objects.create(
            user=self.hospital_admin_user,
            hospital=self.hospital,
            role="HOSPITAL_ADMIN",
            is_active=True,
        )

        # 3. Doctor
        self.doctor_user = User.objects.create_user(
            username="dr.ramesh@apollo.com",
            email="dr.ramesh@apollo.com",
            password=self.password,
            first_name="Ramesh",
            last_name="Kumar",
        )
        HospitalMembership.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            role="DOCTOR",
            is_active=True,
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            department=self.dept,
            employee_code="DOC-APO-001",
            specialization="Interventional Cardiologist",
            consultation_fee=Decimal("150.00"),
            is_active=True,
        )

        # 4. Receptionist
        self.receptionist_user = User.objects.create_user(
            username="priya.reception@apollo.com",
            email="priya.reception@apollo.com",
            password=self.password,
            first_name="Priya",
            last_name="Nair",
        )
        HospitalMembership.objects.create(
            user=self.receptionist_user,
            hospital=self.hospital,
            role="RECEPTIONIST",
            is_active=True,
        )

        # 5. Staff
        self.staff_user = User.objects.create_user(
            username="staff.demo@apollo.com",
            email="staff.demo@apollo.com",
            password=self.password,
            first_name="Arjun",
            last_name="Rao",
        )
        HospitalMembership.objects.create(
            user=self.staff_user,
            hospital=self.hospital,
            role="STAFF",
            is_active=True,
        )

        # 6. Patient
        self.patient_user = User.objects.create_user(
            username="anil.kapoor@example.com",
            email="anil.kapoor@example.com",
            password=self.password,
            first_name="Anil",
            last_name="Kapoor",
        )
        self.patient_profile = PatientProfile.objects.create(
            hospital=self.hospital,
            user=self.patient_user,
            patient_id_code="PAT-2026-0001",
            date_of_birth="1975-04-12",
            gender="MALE",
            contact_number="+91 98111 22334",
            is_active=True,
        )

    def test_login_pages_contain_no_one_click_login_or_prefilled_passwords(self):
        """Verify that login pages have no quick demo buttons or prefilled passwords."""
        login_urls = [
            "doctor_login",
            "hospital_admin_login",
            "receptionist_login",
            "staff_login",
            "super_admin_login",
            "patient_login",
        ]
        for url_name in login_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            content = response.content.decode("utf-8")
            self.assertNotIn("One-Click Demo Login", content)
            self.assertNotIn("1-Click Launch Demo", content)
            self.assertNotIn("Demo Credentials (Testing Only)", content)
            self.assertNotIn('name="quick_demo"', content)
            self.assertNotIn('value="DoctorPass@123"', content)
            self.assertNotIn('value="AdminPass@123"', content)
            self.assertNotIn('value="SuperAdminPass@123"', content)
            self.assertNotIn('value="StaffPass@123"', content)
            self.assertNotIn('value="PatientPass@123"', content)

    def test_quick_demo_bypass_is_completely_rejected(self):
        """Submitting quick_demo=1 should not authenticate any user."""
        response = self.client.post(
            reverse("doctor_login"),
            {"quick_demo": "1", "demo_role": "doctor"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_empty_credentials_rejected(self):
        """Submitting empty email and password shows error message."""
        response = self.client.post(
            reverse("doctor_login"),
            {"email": "", "password": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter both email and password")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_invalid_credentials_rejected(self):
        """Submitting invalid password displays authentication failure error."""
        response = self.client.post(
            reverse("doctor_login"),
            {"email": self.doctor_user.email, "password": "WrongPassword@999"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or password")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_inactive_user_rejected(self):
        """Disabled user account cannot authenticate."""
        self.doctor_user.is_active = False
        self.doctor_user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("doctor_login"),
            {"email": self.doctor_user.email, "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "disabled")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_cross_role_access_denial(self):
        """User cannot log into a portal differing from their assigned role."""
        # Doctor trying to log into Hospital Admin portal
        response = self.client.post(
            reverse("hospital_admin_login"),
            {"email": self.doctor_user.email, "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have access to the Hospital Admin Access portal")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        # Receptionist trying to log into Doctor portal
        response = self.client.post(
            reverse("doctor_login"),
            {"email": self.receptionist_user.email, "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have access to the Doctor Access portal")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_successful_authentication_routes_each_role_correctly(self):
        """Valid credentials route each role to its dedicated dashboard."""
        role_matrix = [
            ("doctor_login", self.doctor_user.email, "doctor_dashboard"),
            ("receptionist_login", self.receptionist_user.email, "receptionist_dashboard"),
            ("hospital_admin_login", self.hospital_admin_user.email, "hospital_admin_dashboard"),
            ("super_admin_login", self.super_admin.email, "super_admin_dashboard"),
            ("staff_login", self.staff_user.email, "staff_dashboard"),
            ("patient_login", self.patient_user.email, "patient_dashboard"),
        ]

        for login_url, email, dashboard_url in role_matrix:
            response = self.client.post(
                reverse(login_url),
                {"email": email, "password": self.password},
            )
            self.assertRedirects(
                response,
                reverse(dashboard_url),
                fetch_redirect_response=False,
                msg_prefix=f"{email} at {login_url} should redirect to {dashboard_url}",
            )
            self.client.logout()

    def test_role_admin_site_access_control(self):
        """Admin sites enforce strict role permissions."""
        from config.admin_sites import (
            super_admin_site,
            hospital_admin_site,
            doctor_admin_site,
            receptionist_admin_site,
        )
        from django.test import RequestFactory
        factory = RequestFactory()

        # Doctor request
        req = factory.get("/admin/doctor/")
        req.user = self.doctor_user
        self.assertTrue(doctor_admin_site.has_permission(req))
        self.assertFalse(super_admin_site.has_permission(req))
        self.assertFalse(hospital_admin_site.has_permission(req))

        # Receptionist request
        req = factory.get("/admin/receptionist/")
        req.user = self.receptionist_user
        self.assertTrue(receptionist_admin_site.has_permission(req))
        self.assertFalse(doctor_admin_site.has_permission(req))
        self.assertFalse(hospital_admin_site.has_permission(req))

        # Hospital Admin request
        req = factory.get("/admin/hospital/")
        req.user = self.hospital_admin_user
        self.assertTrue(hospital_admin_site.has_permission(req))
        self.assertFalse(super_admin_site.has_permission(req))

        # Super Admin request has permission across sites
        req = factory.get("/admin/super/")
        req.user = self.super_admin
        self.assertTrue(super_admin_site.has_permission(req))
