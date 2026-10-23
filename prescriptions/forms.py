from django import forms
from .models import Prescription, PrescriptionMedicine


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["prescription_number", "notes"]
        widgets = {
            "prescription_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Leave empty to auto-generate (e.g. RX-2026-0001)",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "form-control",
                    "placeholder": "General advice, precautions, dietary notes...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prescription_number"].required = False


class PrescriptionMedicineForm(forms.ModelForm):
    class Meta:
        model = PrescriptionMedicine
        fields = [
            "medicine_name",
            "strength",
            "dosage",
            "route",
            "frequency",
            "duration",
            "quantity",
            "instructions",
        ]
        widgets = {
            "medicine_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Paracetamol, Amoxicillin"}),
            "strength": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 500 mg, 10 ml"}),
            "dosage": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 1 tablet, 5 ml"}),
            "route": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Oral, Topical, IV"}),
            "frequency": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 1-0-1 (Twice daily)"}),
            "duration": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 5 days, 1 month"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 10"}),
            "instructions": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. After meals with water"}),
        }