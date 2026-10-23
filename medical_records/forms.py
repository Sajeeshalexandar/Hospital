from django import forms
from .models import MedicalRecord


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            "symptoms",
            "diagnosis",
            "treatment_notes",
            "follow_up_date",
        ]
        widgets = {
            "symptoms": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Observed symptoms and complaints..."}),
            "diagnosis": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Clinical diagnosis..."}),
            "treatment_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Plan, recommendations, diet, lifestyle..."}),
            "follow_up_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }