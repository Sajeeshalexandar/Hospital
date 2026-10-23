from django import forms
from django.utils import timezone
from .models import PatientProfile


class PatientForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    email = forms.EmailField(
        required=False,
        label="Email Address",
        help_text="Optional. If provided, can be used for patient notifications.",
    )

    class Meta:
        model = PatientProfile
        fields = [
            "patient_id_code",
            "date_of_birth",
            "gender",
            "blood_group",
            "contact_number",
            "address",
            "emergency_contact_name",
            "emergency_contact_number",
            "is_active",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "patient_id_code": forms.TextInput(
                attrs={
                    "placeholder": "Leave blank to auto-generate (e.g. PAT-2026-0001)",
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient_id_code"].required = False
        if self.instance and self.instance.pk and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            if not self.instance.user.email.endswith("@patient.local"):
                self.fields["email"].initial = self.instance.user.email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob and dob > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob