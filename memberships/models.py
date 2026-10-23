from django.conf import settings
from django.db import models


class HospitalMembership(models.Model):
    class Role(models.TextChoices):
        HOSPITAL_ADMIN = "HOSPITAL_ADMIN", "Hospital Admin"
        DOCTOR = "DOCTOR", "Doctor"
        RECEPTIONIST = "RECEPTIONIST", "Receptionist"
        STAFF = "STAFF", "Staff"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hospital_memberships",
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "hospital"],
                name="unique_user_hospital_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.hospital} - {self.role}"