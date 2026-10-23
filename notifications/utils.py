from accounts.helpers import get_user_hospital
from .models import Notification


def create_notification(user, title, message, hospital=None, notification_type="SYSTEM"):
    """
    Dispatch an in-app notification to a user.
    """
    if not user:
        return None

    if not hospital:
        hospital = get_user_hospital(user)

    return Notification.objects.create(
        user=user,
        hospital=hospital,
        title=title,
        message=message,
        notification_type=notification_type,
    )
