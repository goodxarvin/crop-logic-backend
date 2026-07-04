from django.db import models
from django.contrib.auth import get_user_model
import uuid
from order.models import Order

user = get_user_model()


class ProvisioningStaus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESING = "processing", "Proccesing"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"


class ProvisioningType(models.TextChoices):
    SUBSCRIPTION = "subscription", "Subscription"
    INSTALLATION_SERVICE = "installation_service", "Installation Service"
    DEVICE = "device", "Device"


class ProvisioningTask(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        user, on_delete=models.PROTECT, related_name="provisioning_tasks"
    )
    order = models.ForeignKey(
        "order.Order", on_delete=models.PROTECT, related_name="provisioning_tasks"
    )
    item = models.JSONField(default=dict, null=True, blank=True)
    farm_id = models.PositiveIntegerField(null=True, blank=True)
    task_type = models.CharField(
        max_length=21,
        choices=ProvisioningType.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=ProvisioningStaus.choices,
        default=ProvisioningStaus.PENDING,
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_type} - {self.status} for user {self.user.email}"
