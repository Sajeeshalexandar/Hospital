from django.shortcuts import render
from accounts.decorators import roles_required
from accounts.helpers import get_user_hospital
from .models import AuditLog


@roles_required("HOSPITAL_ADMIN")
def audit_log_list(request):
    """View security and transactional audit trail for the hospital."""
    hospital = get_user_hospital(request.user)
    if request.user.is_superuser:
        logs = AuditLog.objects.select_related("actor", "hospital").all().order_by("-created_at")
    else:
        logs = AuditLog.objects.select_related("actor", "hospital").filter(hospital=hospital).order_by("-created_at")

    q = request.GET.get("q", "").strip()
    action = request.GET.get("action", "")

    if q:
        logs = logs.filter(
            description__icontains=q
        ) | logs.filter(
            entity_type__icontains=q
        ) | logs.filter(
            actor__email__icontains=q
        )

    if action:
        logs = logs.filter(action=action)

    context = {
        "logs": logs[:100], # Show latest 100 entries
        "hospital": hospital,
        "q": q,
        "action_filter": action,
    }
    return render(request, "audit_logs/list.html", context)
