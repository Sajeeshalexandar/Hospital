"""
Custom Django AdminSite definitions for role-based admin panels.

Provides separate admin panels with dedicated URL endpoints:
- /admin/super/         -> Super Admin panel
- /admin/hospital/      -> Hospital Admin panel
- /admin/doctor/        -> Doctor Admin panel
- /admin/receptionist/  -> Receptionist Admin panel
"""

from django.contrib.admin import AdminSite
from django.apps import apps


class BaseRoleAdminSite(AdminSite):
    """Base AdminSite allowing models to register and customizing role permissions."""

    def register_all(self):
        """Auto-register models robustly without crashing on duplicates."""
        for model in apps.get_models():
            try:
                self.register(model)
            except Exception:
                pass


class SuperAdminSite(BaseRoleAdminSite):
    site_header = "MediSaaS Super Admin Control Center"
    site_title = "Super Admin"
    index_title = "Platform & Global Multi-Tenant Administration"

    def has_permission(self, request):
        return request.user.is_active and (request.user.is_superuser or request.user.is_staff)


class HospitalAdminSite(BaseRoleAdminSite):
    site_header = "MediSaaS Hospital Administrator Panel"
    site_title = "Hospital Admin"
    index_title = "Hospital Administration & Resource Management"

    def has_permission(self, request):
        if not request.user.is_active or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        from accounts.helpers import get_user_role
        return get_user_role(request.user) == "HOSPITAL_ADMIN"


class DoctorAdminSite(BaseRoleAdminSite):
    site_header = "MediSaaS Doctor Clinical Workspace"
    site_title = "Doctor Admin"
    index_title = "Clinical Records, Consultations & Prescriptions"

    def has_permission(self, request):
        if not request.user.is_active or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        from accounts.helpers import get_user_role
        return get_user_role(request.user) == "DOCTOR"


class ReceptionistAdminSite(BaseRoleAdminSite):
    site_header = "MediSaaS Receptionist Desk & Front Office"
    site_title = "Receptionist Admin"
    index_title = "Front Desk, Patient Admissions & Appointments"

    def has_permission(self, request):
        if not request.user.is_active or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        from accounts.helpers import get_user_role
        return get_user_role(request.user) in ["RECEPTIONIST", "STAFF"]


super_admin_site = SuperAdminSite(name='super_admin')
hospital_admin_site = HospitalAdminSite(name='hospital_admin')
doctor_admin_site = DoctorAdminSite(name='doctor_admin')
receptionist_admin_site = ReceptionistAdminSite(name='receptionist_admin')

# Register models
for site in (
    super_admin_site,
    hospital_admin_site,
    doctor_admin_site,
    receptionist_admin_site,
):
    site.register_all()
