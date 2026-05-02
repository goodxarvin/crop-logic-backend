import uuid as uuid_lib

from django.db import models

from farm_hub.models import FarmHub
from .enums import FarmerPriority


class FarmerCalendarZone(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(FarmHub, on_delete=models.CASCADE, related_name="calendar_zones")
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farmer_calendar_zones"
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(fields=["farm", "value"], name="uniq_farmer_calendar_zone_per_farm"),
        ]

    def __str__(self):
        return self.label


class FarmerCalendarTag(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(FarmHub, on_delete=models.CASCADE, related_name="calendar_tags")
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farmer_calendar_tags"
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(fields=["farm", "value"], name="uniq_farmer_calendar_tag_per_farm"),
        ]

    def __str__(self):
        return self.label


class FarmerCalendarEvent(models.Model):
    PRIORITY_HIGH = FarmerPriority.HIGH
    PRIORITY_MEDIUM = FarmerPriority.MEDIUM
    PRIORITY_LOW = FarmerPriority.LOW
    PRIORITY_CHOICES = FarmerPriority.choices

    STATUS_OPEN = "open"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_DONE, "Done"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(FarmHub, on_delete=models.CASCADE, related_name="calendar_events")
    zone = models.ForeignKey(FarmerCalendarZone, on_delete=models.PROTECT, related_name="events", null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    deadline = models.BigIntegerField(null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    extended_props = models.JSONField(default=dict, blank=True)
    tags = models.ManyToManyField(FarmerCalendarTag, related_name="events", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farmer_calendar_events"
        ordering = ["scheduled_date", "start", "time", "created_at"]

    def __str__(self):
        return self.title
