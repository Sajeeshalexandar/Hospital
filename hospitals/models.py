from django.db import models


class HospitalTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    template_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    preview_image = models.ImageField(
        upload_to="templates/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Hospital(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(max_length=200)
    registration_number = models.CharField(
        max_length=50,
        unique=True,
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=15, blank=True)

    template = models.ForeignKey(
        HospitalTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hospitals",
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class HospitalSettings(models.Model):
    hospital = models.OneToOneField(
        Hospital,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    timezone = models.CharField(
        max_length=50,
        default="Asia/Kolkata",
    )
    currency = models.CharField(max_length=3, default="INR")
    appointment_duration_minutes = models.PositiveSmallIntegerField(
        default=30,
    )
    allow_online_appointments = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings - {self.hospital.name}"