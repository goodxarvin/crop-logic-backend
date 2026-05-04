import uuid as uuid_lib

from django.db import models


class SubscriptionPlan(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_subscription_plans"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AccessFeature(models.Model):
    PAGE = "page"
    WIDGET = "widget"
    ACTION = "action"
    FEATURE_TYPES = [
        (PAGE, "Page"),
        (WIDGET, "Widget"),
        (ACTION, "Action"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=150, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    feature_type = models.CharField(max_length=32, choices=FEATURE_TYPES, default=PAGE)
    default_enabled = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_features"
        ordering = ["name"]

    def __str__(self):
        return self.code


class AccessRule(models.Model):
    ALLOW = "allow"
    DENY = "deny"
    EFFECTS = [
        (ALLOW, "Allow"),
        (DENY, "Deny"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=150, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    priority = models.PositiveIntegerField(default=100)
    effect = models.CharField(max_length=16, choices=EFFECTS, default=ALLOW)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    features = models.ManyToManyField("AccessFeature", related_name="rules", blank=True)
    subscription_plans = models.ManyToManyField("SubscriptionPlan", related_name="access_rules", blank=True)
    farm_types = models.ManyToManyField("farm_hub.FarmType", related_name="access_rules", blank=True)
    products = models.ManyToManyField("farm_hub.Product", related_name="access_rules", blank=True)
    sensor_catalogs = models.ManyToManyField("device_hub.SensorCatalog", related_name="access_rules", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_rules"
        ordering = ["priority", "name"]

    def __str__(self):
        return self.code


class FarmAccessProfile(models.Model):
    farm = models.OneToOneField("farm_hub.FarmHub", on_delete=models.CASCADE, related_name="access_profile")
    subscription_plan = models.ForeignKey(
        "SubscriptionPlan",
        on_delete=models.SET_NULL,
        related_name="farm_access_profiles",
        null=True,
        blank=True,
    )
    profile_data = models.JSONField(default=dict, blank=True)
    resolved_from_profile = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_access_profiles"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Access profile for {self.farm_id}"
