from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def superadmin_required(view_func):
    """
    Decorator: only allows users where is_superuser=True.
    All other users are sent back to login with an error message.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_superuser:
            messages.error(request, "You do not have Super Admin access.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped


def roles_required(*roles):
    """
    Decorator: allows access if the user has an active membership matching
    any of the specified roles, or if user is a superuser.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            from accounts.helpers import get_user_role
            role = get_user_role(request.user)

            if role not in roles:
                messages.error(
                    request,
                    "You do not have permission to access this page.",
                )
                return redirect("login")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def _membership_required(required_role):
    """
    Internal factory that creates a single role-checking decorator.
    """
    return roles_required(required_role)


# Ready-to-use decorators for each role
hospital_admin_required = _membership_required("HOSPITAL_ADMIN")
doctor_required          = _membership_required("DOCTOR")
receptionist_required    = _membership_required("RECEPTIONIST")
staff_required           = _membership_required("STAFF")
