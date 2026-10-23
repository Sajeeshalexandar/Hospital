from django import forms
from django.contrib.auth import get_user_model
from departments.models import Department
from .models import DoctorProfile, DoctorAvailability

User = get_user_model()


class DoctorCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True, min_length=6)

    class Meta:
        model = DoctorProfile
        fields = [
            "department",
            "employee_code",
            "qualification",
            "specialization",
            "experience_years",
            "consultation_fee",
            "op_commission_percentage",
            "contact_number",
            "is_active",
        ]

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields["department"].queryset = Department.objects.filter(
                hospital=hospital, is_active=True
            )

    def clean_email(self):
        email = self.cleaned_data.get("email").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email


class DoctorEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "department",
            "employee_code",
            "qualification",
            "specialization",
            "experience_years",
            "consultation_fee",
            "op_commission_percentage",
            "contact_number",
            "is_active",
        ]

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
        if hospital:
            self.fields["department"].queryset = Department.objects.filter(
                hospital=hospital
            )


class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = [
            "weekday",
            "start_time",
            "end_time",
            "effective_from",
            "effective_until",
            "is_active",
        ]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "effective_from": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "effective_until": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end and end <= start:
            raise forms.ValidationError("End time must be later than start time.")

        eff_from = cleaned_data.get("effective_from")
        eff_until = cleaned_data.get("effective_until")
        if eff_from and eff_until and eff_until < eff_from:
            raise forms.ValidationError("Effective until date must not precede start date.")

        return cleaned_data