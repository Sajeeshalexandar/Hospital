from django import forms
from .models import SubscriptionPlan, HospitalSubscription


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "name", "code", "price", "currency",
            "duration_days", "max_users", "max_patients",
            "features", "is_active",
        ]


class HospitalSubscriptionForm(forms.ModelForm):
    class Meta:
        model = HospitalSubscription
        fields = [
            "hospital", "plan", "status", "start_date",
            "end_date", "auto_renew",
        ]

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and end <= start:
            raise forms.ValidationError(
                "The subscription end date must be after its start date."
            )

        return cleaned_data