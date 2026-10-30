from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Notification


@login_required(login_url="portals_gateway")
def notification_list(request):
    """View notifications for the logged-in user."""
    user_notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_count = user_notifications.filter(is_read=False).count()

    context = {
        "notifications": user_notifications,
        "unread_count": unread_count,
    }
    return render(request, "notifications/list.html", context)


@login_required(login_url="portals_gateway")
def mark_as_read(request, pk):
    """Mark a single notification as read."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.read_at = timezone.now()
    notif.save()
    return redirect("notification_list")


@login_required(login_url="portals_gateway")
def mark_all_read(request):
    """Mark all user notifications as read."""
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        messages.success(request, "All notifications marked as read.")
    return redirect("notification_list")
