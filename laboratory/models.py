from django.db import models
from django.conf import settings


class LabTestOrder(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        COLLECTED = "COLLECTED", "Sample Collected"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.PROTECT,
        related_name="lab_orders",
    )
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.PROTECT,
        related_name="lab_orders",
    )
    doctor = models.ForeignKey(
        "doctors.DoctorProfile",
        on_delete=models.PROTECT,
        related_name="lab_orders",
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lab_orders",
    )
    test_name = models.CharField(max_length=200)
    clinical_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    ordered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_name} - {self.patient}"


class LabReport(models.Model):
    order = models.ForeignKey(
        LabTestOrder,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.PROTECT,
        related_name="lab_reports",
    )
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.PROTECT,
        related_name="lab_reports",
    )
    report_number = models.CharField(max_length=40)
    result_summary = models.TextField(blank=True)
    report_file = models.FileField(
        upload_to="lab_reports/",
        blank=True,
        null=True,
    )
    remarks = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="verified_lab_reports",
    )
    tested_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hospital", "report_number"],
                name="unique_lab_report_per_hospital",
            )
        ]

    def __str__(self):
        return self.report_number