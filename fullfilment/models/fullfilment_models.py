from django.db import models
from address.models import AddressType
from django.core.exceptions import ValidationError
from uuid import uuid4


class ShipmentStatus(models.TextChoices):
    BACKORDERED = "backordered", "Backordered"
    PREPARING = "preparing", "Preparing"
    PACKING = "packed", "Packed"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"


class InstallationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Shipment(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    order = models.ForeignKey(
        "order.Order", on_delete=models.PROTECT, related_name="shipments"
    )
    address = models.ForeignKey(
        "address.Address", on_delete=models.PROTECT, related_name="shipments"
    )
    carrier = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=ShipmentStatus.choices, default=ShipmentStatus.PREPARING
    )
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Shipment for Order {self.order.pk}"


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="shipment_items"
    )
    cart_item = models.JSONField(default=dict, null=True, blank=True)
    shipping_address = models.OneToOneField(
        "address.Address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shipment_item",
    )
    quantity = models.PositiveIntegerField(default=1)
    allocated_device_serial_number = models.CharField(
        max_length=100, blank=True, null=True
    )

    def __str__(self):
        return f"{self.quantity} of {self.cart_item.get('sku_id')} for Shipment {self.shipment.id}"

    def clean(self):
        super().clean()

        if (
            self.shipping_address
            and getattr(self.shipping_address, "address_type", None)
            != AddressType.SHIPPING
        ):
            raise ValidationError(
                {"shipping_address": "The provided address is not a shipping address."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class InstallationRequest(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    cart_item = models.JSONField(default=dict, null=True, blank=True)
    farm = models.ForeignKey("farm_hub.FarmHub", on_delete=models.PROTECT)
    farm_address = models.OneToOneField(
        "address.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installation_request",
    )
    status = models.CharField(
        max_length=20,
        choices=InstallationStatus.choices,
        default=InstallationStatus.PENDING,
    )
    scheduled_for = models.DateTimeField(null=True, blank=True)
    assigned_team = models.CharField(max_length=100, blank=True, null=True)

    installed_at = models.DateTimeField(null=True, blank=True)
    installer_notes = models.TextField(blank=True, null=True)

    def clean(self):
        super().clean()

        if (
            self.farm_address
            and getattr(self.farm_address, "address_type", None)
            != AddressType.FARM_LOCATION
        ):
            raise ValidationError(
                {"farm_address": "The provided address is not a farm address."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
