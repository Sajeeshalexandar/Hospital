from accounts.helpers import get_user_hospital
from .models import AuditLog


def get_client_ip(request):
    """Safely extract remote IP address from request headers."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit(request, action, entity_type, entity_id="", description="", hospital=None):
    """
    Trusted backend audit logger.
    Captures actor, hospital tenant, action, entity, IP address, and details.
    """
    try:
        actor = request.user if request and request.user.is_authenticated else None
        if not hospital and actor:
            hospital = get_user_hospital(actor)

        ip = get_client_ip(request)

        return AuditLog.objects.create(
            hospital=hospital,
            actor=actor,
            action=action.upper(),
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            ip_address=ip,
        )
    except Exception:
        # Never crash user transactions due to audit log failures
        return None
