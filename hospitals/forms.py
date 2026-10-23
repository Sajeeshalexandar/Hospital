from django import forms
from .models import Hospital, HospitalSettings, HospitalTemplate


class HospitalTemplateForm(forms.ModelForm):
    class Meta:
        model = HospitalTemplate
        fields = [
            "name", "template_code", "description",
            "preview_image", "is_active",
        ]


class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = [
            "name", "registration_number", "email", "phone",
            "address", "city", "state", "country", "postal_code",
            "template", "status",
        ]


class HospitalSettingsForm(forms.ModelForm):
    class Meta:
        model = HospitalSettings
        fields = [
            "timezone", "currency",
            "appointment_duration_minutes",
            "allow_online_appointments",
        ]