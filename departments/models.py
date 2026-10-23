from django.db import models


class Department(models.Model):
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="departments",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hospital", "name"],
                name="unique_department_per_hospital",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"