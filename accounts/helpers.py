from memberships.models import HospitalMembership


def get_user_membership(user):
    """
    Returns the active HospitalMembership object for the given user,
    or None if the user has no active membership.

    NEVER trust a role from the browser. Always read it from the database
    using this function.
    """
    try:
        return HospitalMembership.objects.select_related("hospital").get(
            user=user,
            is_active=True,
        )
    except HospitalMembership.DoesNotExist:
        return None
    except HospitalMembership.MultipleObjectsReturned:
        # Safety: if somehow there are multiple, return None and log it
        # (This should not happen because of the unique constraint, but
        # we handle it anyway.)
        return None


def get_user_hospital(user):
    """
    Returns the Hospital object for the given user's active membership,
    or None.

    Use this everywhere you need to filter querysets by the current user's
    hospital. Example:
        hospital = get_user_hospital(request.user)
        patients = PatientProfile.objects.filter(hospital=hospital)
    """
    membership = get_user_membership(user)
    return membership.hospital if membership else None


def get_user_role(user):
    """
    Returns the role string (e.g. 'HOSPITAL_ADMIN', 'DOCTOR') for the
    given user's active membership, or None.

    For Super Admins check user.is_superuser instead.
    """
    membership = get_user_membership(user)
    return membership.role if membership else None


def get_user_patient(user):
    """
    Returns the active PatientProfile object for the given user, or None.
    """
    from patients.models import PatientProfile
    return PatientProfile.objects.filter(user=user, is_active=True).select_related("hospital").first()

