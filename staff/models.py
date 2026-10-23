from django.db import models


class StaffProfile(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="staff_profiles",
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="staff_members",
    )
    employee_code = models.CharField(max_length=30)
    job_title = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    date_of_joining = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hospital", "employee_code"],
                name="unique_staff_code_per_hospital",
            )
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.job_title}"