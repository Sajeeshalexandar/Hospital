from django import forms
from .models import HospitalMembership


class HospitalMembershipForm(forms.ModelForm):
    class Meta:
        model = HospitalMembership
        fields = ["user", "hospital", "role", "is_active"]