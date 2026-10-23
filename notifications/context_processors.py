def unread_notifications(request):
    """Provide unread notifications count across all templates."""
    if hasattr(request, "user") and request.user.is_authenticated:
        try:
            return {"unread_notifications_count": request.user.notifications.filter(is_read=False).count()}
        except Exception:
            return {"unread_notifications_count": 0}
    return {"unread_notifications_count": 0}
