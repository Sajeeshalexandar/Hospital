from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class PatientProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        NOT_SPECIFIED = "NOT_SPECIFIED", "Prefer not to say"

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_profiles",
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="patients",
    )
    patient_id_code = models.CharField(max_length=30)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices)
    contact_number = models.CharField(max_length=20)
    address = models.TextField()
    blood_group = models.CharField(
        max_length=3,
        choices=BloodGroup.choices,
        blank=True,
    )
    emergency_contact_name = models.CharField(
        max_length=150,
        blank=True,
    )
    emergency_contact_number = models.CharField(
        max_length=20,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hospital", "patient_id_code"],
                name="unique_patient_code_per_hospital",
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError(
                {"date_of_birth": "Date of birth cannot be in the future."}
            )

    def __str__(self):
        return f"{self.patient_id_code} - {self.hospital.name}"