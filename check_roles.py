import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.helpers import get_user_membership, get_user_role, get_user_patient
from accounts.models import User

redirects = {
    "HOSPITAL_ADMIN": "hospital_admin_dashboard",
    "DOCTOR": "doctor_dashboard",
    "RECEPTIONIST": "receptionist_dashboard",
    "STAFF": "staff_dashboard",
}

test_cases = [
    ('superadmin@medisaas.com', 'Super Admin'),
    ('apollo.admin@medisaas.com', 'Hospital Admin'),
    ('dr.ramesh@apollo.com', 'Doctor'),
    ('priya.reception@apollo.com', 'Receptionist'),
    ('anil.kapoor@example.com', 'Patient'),
    ('sunita.patel@example.com', 'Patient 2'),
]

for email, label in test_cases:
    try:
        u = User.objects.get(email=email)
        membership = get_user_membership(u)
        patient = get_user_patient(u)
        role = get_user_role(u)
        print(f"[{label}] {email}")
        print(f"  is_superuser={u.is_superuser}, role={role}, patient={patient is not None}")
        if u.is_superuser:
            dest = "super_admin_dashboard"
        elif patient:
            dest = "patient_dashboard"
        elif membership:
            dest = redirects.get(membership.role, "UNKNOWN")
        else:
            dest = "NO_ROLE -> logout!"
        print(f"  --> {dest}")
        print()
    except User.DoesNotExist:
        print(f"[{label}] USER NOT FOUND: {email}\n")
