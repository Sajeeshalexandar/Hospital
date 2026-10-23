from django import forms
from .models import Notification


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = [
            "user", "hospital",
            "notification_type", "title", "message",
        ]