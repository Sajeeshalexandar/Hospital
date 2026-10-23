from django import forms
from patients.models import PatientProfile
from doctors.models import DoctorProfile
from departments.models import Department
from .models import Appointment


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "patient",
            "doctor",
            "department",
            "start_at",
            "end_at",
            "reason_for_visit",
        ]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "reason_for_visit": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Chief symptoms, reason for consultation..."}),
        }

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields["patient"].queryset = PatientProfile.objects.filter(
                hospital=hospital, is_active=True
            ).select_related("user")
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(
                hospital=hospital, is_active=True
            ).select_related("user", "department")
            self.fields["department"].queryset = Department.objects.filter(
                hospital=hospital, is_active=True
            )

        self.fields["patient"].label_from_instance = (
            lambda obj: f"{obj.user.get_full_name() if obj.user else 'Patient'} ({obj.patient_id_code})"
        )
        self.fields["doctor"].label_from_instance = (
            lambda obj: f"Dr. {obj.user.get_full_name()} - {obj.specialization} ({obj.department.name})"
        )
        self.fields["department"].label_from_instance = lambda obj: obj.name

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_at")
        end = cleaned_data.get("end_at")
        doctor = cleaned_data.get("doctor")

        if start and end:
            if end <= start:
                raise forms.ValidationError("Appointment end time must be after start time.")

            # Overlap conflict detection
            if doctor:
                conflicts = Appointment.objects.filter(
                    doctor=doctor,
                    status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
                    start_at__lt=end,
                    end_at__gt=start,
                )
                if self.instance and self.instance.pk:
                    conflicts = conflicts.exclude(pk=self.instance.pk)

                if conflicts.exists():
                    conf = conflicts.first()
                    raise forms.ValidationError(
                        f"Schedule Conflict! Dr. {doctor.user.get_full_name()} already has an appointment "
                        f"from {conf.start_at.strftime('%H:%M')} to {conf.end_at.strftime('%H:%M')} on {conf.start_at.strftime('%d %b %Y')}."
                    )

        return cleaned_data


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["status", "cancellation_reason"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "cancellation_reason": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Required if cancelling..."}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        reason = cleaned_data.get("cancellation_reason")

        if status == Appointment.Status.CANCELLED and not reason:
            raise forms.ValidationError({"cancellation_reason": "Please provide a reason for cancelling."})

        return cleaned_data