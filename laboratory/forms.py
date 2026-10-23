from django import forms
from patients.models import PatientProfile
from doctors.models import DoctorProfile
from appointments.models import Appointment
from .models import LabTestOrder, LabReport


class LabTestOrderForm(forms.ModelForm):
    class Meta:
        model = LabTestOrder
        fields = ["patient", "doctor", "appointment", "test_name", "clinical_notes"]
        widgets = {
            "test_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Complete Blood Count (CBC), Lipid Profile, Chest X-Ray"}),
            "clinical_notes": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Clinical indications, fasting requirements..."}),
        }

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields["patient"].queryset = PatientProfile.objects.filter(
                hospital=hospital, is_active=True
            ).select_related("user")
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(
                hospital=hospital, is_active=True
            ).select_related("user")
            self.fields["appointment"].queryset = Appointment.objects.filter(
                hospital=hospital
            ).select_related("patient", "doctor")
            self.fields["appointment"].required = False

        self.fields["patient"].label_from_instance = (
            lambda obj: f"{obj.user.get_full_name() if obj.user else 'Patient'} ({obj.patient_id_code})"
        )
        self.fields["doctor"].label_from_instance = (
            lambda obj: f"Dr. {obj.user.get_full_name()} ({obj.department.name})"
        )


class LabReportForm(forms.ModelForm):
    class Meta:
        model = LabReport
        fields = [
            "report_number",
            "result_summary",
            "report_file",
            "remarks",
            "tested_at",
            "reported_at",
        ]
        widgets = {
            "report_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Leave blank to auto-generate (e.g. LAB-2026-0001)"}),
            "result_summary": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "Key diagnostic values, findings, reference ranges..."}),
            "remarks": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Pathologist remarks, recommendations..."}),
            "tested_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "reported_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["report_number"].required = False