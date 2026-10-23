from django.db import models


class Prescription(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        CANCELLED = "CANCELLED", "Cancelled"

    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.PROTECT,
        related_name="prescriptions",
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        related_name="prescriptions",
    )
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.PROTECT,
        related_name="prescriptions",
    )
    doctor = models.ForeignKey(
        "doctors.DoctorProfile",
        on_delete=models.PROTECT,
        related_name="prescriptions",
    )
    prescription_number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hospital", "prescription_number"],
                name="unique_prescription_per_hospital",
            )
        ]

    def __str__(self):
        return self.prescription_number


class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="medicines",
    )
    medicine_name = models.CharField(max_length=200)
    strength = models.CharField(max_length=100, blank=True)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=50, blank=True)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    instructions = models.TextField(blank=True)

    def __str__(self):
        return self.medicine_name