from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


ROLE_LOGIN_URLS = {
    "SUPER_ADMIN": "super_admin_login",
    "HOSPITAL_ADMIN": "hospital_admin_login",
    "DOCTOR": "doctor_login",
    "RECEPTIONIST": "receptionist_login",
    "STAFF": "staff_login",
    "PATIENT": "patient_login",
}


def superadmin_required(view_func):
    """Only superusers (is_superuser=True) can access this view."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(ROLE_LOGIN_URLS["SUPER_ADMIN"])
        if not request.user.is_superuser:
            messages.error(request, "You do not have Super Admin access.")
            return redirect(ROLE_LOGIN_URLS["SUPER_ADMIN"])
        return view_func(request, *args, **kwargs)
    return _wrapped


def roles_required(*roles):
    """
    STRICT role check. Allows access only if user has an active HospitalMembership
    with one of the specified roles. Superusers are NOT exempt — they must use
    their own super_admin_dashboard. This prevents privilege escalation.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(ROLE_LOGIN_URLS[roles[0]] if roles else "portals_gateway")
            from accounts.helpers import get_user_role
            role = get_user_role(request.user)
            if role not in roles:
                messages.error(
                    request,
                    "You do not have permission to access this page.",
                )
                return redirect(ROLE_LOGIN_URLS[roles[0]] if roles else "portals_gateway")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def _membership_required(required_role):
    return roles_required(required_role)


# Ready-to-use decorators for each role
hospital_admin_required = _membership_required("HOSPITAL_ADMIN")
doctor_required          = _membership_required("DOCTOR")
receptionist_required    = _membership_required("RECEPTIONIST")
staff_required           = _membership_required("STAFF")


def patient_required(view_func):
    """Allows access only to authenticated Patient users."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(ROLE_LOGIN_URLS["PATIENT"])
        from patients.models import PatientProfile
        if not PatientProfile.objects.filter(user=request.user, is_active=True).exists():
            messages.error(request, "Access restricted to authenticated patients.")
            return redirect(ROLE_LOGIN_URLS["PATIENT"])
        return view_func(request, *args, **kwargs)
    return _wrapped
