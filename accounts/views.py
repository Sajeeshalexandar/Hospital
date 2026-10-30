from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from accounts.helpers import get_user_membership

ROLE_CONFIGS = {
    "doctor": {
        "slug": "doctor",
        "login_url_name": "doctor_login",
        "role_key": "DOCTOR",
        "title": "Doctor Medical Workspace",
        "subtitle": "Access consultation queue, patient electronic records, prescriptions & lab orders",
        "badge": "Doctor Access",
        "badge_color": "info",
        "demo_email": "dr.ramesh@apollo.com",
        "demo_password": "DoctorPass@123",
        "demo_name": "Dr. Ramesh Gupta (Cardiologist)",
        "icon": "bi-stethoscope",
        "target_url": "doctor_dashboard",
    },
    "receptionist": {
        "slug": "receptionist",
        "login_url_name": "receptionist_login",
        "role_key": "RECEPTIONIST",
        "title": "Receptionist Front Desk Portal",
        "subtitle": "OPD patient admissions, appointment check-ins, and cashier billing collection",
        "badge": "Receptionist Access",
        "badge_color": "warning",
        "demo_email": "priya.reception@apollo.com",
        "demo_password": "StaffPass@123",
        "demo_name": "Priya Sharma (Front Desk / Cashier)",
        "icon": "bi-person-badge",
        "target_url": "receptionist_dashboard",
    },
    "hospital-admin": {
        "slug": "hospital-admin",
        "login_url_name": "hospital_admin_login",
        "role_key": "HOSPITAL_ADMIN",
        "title": "Hospital Administrator Console",
        "subtitle": "Doctor rosters, department management, billing overview, assessment & operational analytics",
        "badge": "Hospital Admin Access",
        "badge_color": "primary",
        "demo_email": "apollo.admin@medisaas.com",
        "demo_password": "AdminPass@123",
        "demo_name": "Apollo Life Care Administrator",
        "icon": "bi-building-gear",
        "target_url": "hospital_admin_dashboard",
    },
    "super-admin": {
        "slug": "super-admin",
        "login_url_name": "super_admin_login",
        "role_key": "SUPER_ADMIN",
        "title": "Super Admin Control Center",
        "subtitle": "Multi-hospital SaaS governance, subscription plans, tenant health & global audit trail",
        "badge": "Super Admin Access",
        "badge_color": "danger",
        "demo_email": "superadmin@medisaas.com",
        "demo_password": "SuperAdminPass@123",
        "demo_name": "Platform Super Administrator",
        "icon": "bi-shield-lock",
        "target_url": "super_admin_dashboard",
    },
    "patient": {
        "slug": "patient",
        "login_url_name": "patient_login",
        "role_key": "PATIENT",
        "title": "Patient Healthcare Portal",
        "subtitle": "Access your appointments, clinical records, digital prescriptions, lab reports and invoices",
        "badge": "Patient Access",
        "badge_color": "success",
        "demo_email": "anil.kapoor@example.com",
        "demo_password": "PatientPass@123",
        "demo_name": "Anil Kapoor (Patient PAT-2026-0001)",
        "icon": "bi-person-heart",
        "target_url": "patient_dashboard",
    },
    "staff": {
        "slug": "staff",
        "login_url_name": "staff_login",
        "role_key": "STAFF",
        "title": "Hospital Staff Portal",
        "subtitle": "OPD patient admissions, appointment check-ins, cashier payments and permitted hospital functions",
        "badge": "Staff Access",
        "badge_color": "warning",
        "demo_email": "staff.demo@apollo.com",
        "demo_password": "StaffPass@123",
        "demo_name": "Arjun Rao (Hospital Staff)",
        "icon": "bi-people",
        "target_url": "staff_dashboard",
    },
}


def _authenticate_and_login(request, email, password):
    """Authenticate user with email/username and log them in."""
    user = authenticate(request, username=email, password=password)
    if user is None:
        from accounts.models import User as AppUser
        try:
            db_user = AppUser.objects.get(email=email)
            user = authenticate(request, username=db_user.username, password=password)
        except AppUser.DoesNotExist:
            user = None
    return user


def _role_key_for_user(user):
    if user.is_superuser:
        return "SUPER_ADMIN"

    from patients.models import PatientProfile

    if PatientProfile.objects.filter(user=user, is_active=True).exists():
        return "PATIENT"

    membership = get_user_membership(user)
    return membership.role if membership else None


def _role_login(request, role_slug, template):
    """
    Shared authentication logic for role-specific login views.
    Renders the given template instead of the generic login.html.
    """
    role_info = ROLE_CONFIGS.get(role_slug)

    if request.user.is_authenticated and role_info:
        if _role_key_for_user(request.user) == role_info["role_key"]:
            return redirect(role_info["target_url"])

    # Handle 1-click demo login
    if request.method == "POST" and request.POST.get("quick_demo") == "1":
        cfg = ROLE_CONFIGS.get(role_slug)
        if cfg:
            user = _authenticate_and_login(request, cfg["demo_email"], cfg["demo_password"])
            if user and user.is_active and _role_key_for_user(user) == cfg["role_key"]:
                login(request, user)
                messages.success(request, f"Signed in as {cfg['demo_name']}.")
                return redirect(cfg["target_url"])
            messages.error(
                request,
                "The demo account is unavailable or has the wrong role. Run `python manage.py seed_demo_data` and try again.",
            )

    if request.method == "POST":
        if request.POST.get("quick_demo") == "1":
            return render(request, template, {"role_info": role_info})

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
            return render(request, template, {"role_info": role_info})

        user = _authenticate_and_login(request, email, password)

        if user is None:
            messages.error(request, "Invalid email or password. Please try again.")
            return render(request, template, {"role_info": role_info})

        if not user.is_active:
            messages.error(request, "Your account has been disabled. Contact your administrator.")
            return render(request, template, {"role_info": role_info})

        if role_info and _role_key_for_user(user) != role_info["role_key"]:
            messages.error(
                request,
                f"This account does not have access to the {role_info['badge']} portal.",
            )
            return render(request, template, {"role_info": role_info})

        login(request, user)

        if role_info and role_info.get("target_url"):
            return redirect(role_info["target_url"])

        return redirect("dashboard_dispatch")

    context = {"role_info": role_info}
    return render(request, template, context)


def login_redirect(request):
    """Redirect the obsolete generic login URL to the role portal directory."""
    return redirect("portals_gateway")


def doctor_login_view(request):
    """Dedicated login URL for Doctors: /login/doctor/"""
    return _role_login(request, role_slug="doctor", template="accounts/login_doctor.html")


def receptionist_login_view(request):
    """Dedicated login URL for Receptionists: /login/receptionist/"""
    return _role_login(request, role_slug="receptionist", template="accounts/login_receptionist.html")


def hospital_admin_login_view(request):
    """Dedicated login URL for Hospital Admins: /login/hospital-admin/"""
    return _role_login(request, role_slug="hospital-admin", template="accounts/login_hospital_admin.html")


def super_admin_login_view(request):
    """Dedicated login URL for Super Admins: /login/super-admin/"""
    return _role_login(request, role_slug="super-admin", template="accounts/login_super_admin.html")


def patient_login_view(request):
    """Dedicated login URL for Patients: /login/patient/"""
    return _role_login(request, role_slug="patient", template="accounts/login_patient.html")


def staff_login_view(request):
    """Dedicated login URL for Hospital Staff: /login/staff/"""
    return _role_login(request, role_slug="staff", template="accounts/login_staff.html")


def logout_view(request):
    """Log out and return to the login page for the user's role."""
    role_key = _role_key_for_user(request.user) if request.user.is_authenticated else None
    destination = next(
        (
            config["login_url_name"]
            for config in ROLE_CONFIGS.values()
            if config["role_key"] == role_key
        ),
        "portals_gateway",
    )
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect(destination)
