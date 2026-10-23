from django import forms
from django.contrib.auth import get_user_model
from memberships.models import HospitalMembership
from .models import StaffProfile

User = get_user_model()


class StaffCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True, min_length=6)

    ROLE_CHOICES = [
        (HospitalMembership.Role.RECEPTIONIST, "Receptionist (Front Desk)"),
        (HospitalMembership.Role.STAFF, "General Staff / Nurse / Admin"),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, initial=HospitalMembership.Role.RECEPTIONIST)

    class Meta:
        model = StaffProfile
        fields = [
            "employee_code",
            "job_title",
            "contact_number",
            "date_of_joining",
            "is_active",
        ]
        widgets = {
            "date_of_joining": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email


class StaffEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    ROLE_CHOICES = [
        (HospitalMembership.Role.RECEPTIONIST, "Receptionist (Front Desk)"),
        (HospitalMembership.Role.STAFF, "General Staff / Nurse / Admin"),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = StaffProfile
        fields = [
            "employee_code",
            "job_title",
            "contact_number",
            "date_of_joining",
            "is_active",
        ]
        widgets = {
            "date_of_joining": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            membership = HospitalMembership.objects.filter(
                user=self.instance.user,
                hospital=self.instance.hospital,
                is_active=True
            ).first()
            if membership:
                self.fields["role"].initial = membership.role